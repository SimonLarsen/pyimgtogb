#!/usr/bin/env python3
import argparse
import png
import numpy as np
import itertools
import export
from string import Template


def convert_tile(data, x, y):
    px, py = x*8, y*8
    td = data[px:px+8, py:py+8]

    out = []
    for iy in range(8):
        b0, b1 = 0, 0
        for ix in range(8):
            v = td[ix, iy]

            b0 |= (v & 1) << (7 - ix)
            b1 |= ((v & 2) >> 1) << (7 - ix)

        out.append(b0)
        out.append(b1)
    return tuple(out)


def convert_tile_color(data, palette, x, y):
    m = {}
    for i in range(len(palette)):
        m[palette[i]] = i

    px, py = x*8, y*8
    td = data[px:px+8, py:py+8]

    out = []
    for iy in range(8):
        b0, b1 = 0, 0
        for ix in range(8):
            v = m[td[ix, iy]]

            b0 |= (v & 1) << (7 - ix)
            b1 |= ((v & 2) >> 1) << (7 - ix)

        out.append(b0)
        out.append(b1)
    return tuple(out)


def make_color_palettes(data, colors, tiles_x, tiles_y):
    palette_map = []
    palettes = []
    for y in range(tiles_y):
        for x in range(tiles_x):
            px, py = x*8, y*8
            td = data[px:px+8, py:py+8]
            values = np.unique(td)
            if len(values) > 4:
                raise ValueError("Tile ({},{}) contains more than 4 different colors.".format(x, y))

            index = -1
            for i in range(len(palette_map)):
                noverlap = sum(v in palette_map[i] for v in values)
                if len(palette_map[i]) + len(values) - noverlap <= 4:
                    index = i
                    break

            if index == -1:
                index = len(palette_map)
                palette_map.append([])

            for v in values:
                if v not in palette_map[index]:
                    palette_map[index].append(v)

            palettes.append(index)

    return palettes, palette_map


def rgb_to_5bit(r, g, b):
    r = round(r  / 255 * 31)
    g = round(g  / 255 * 31)
    b = round(b  / 255 * 31)
    return r + (g << 5) + (b << 10)


def make_dx_palettes(data, data_dx, colors, tiles_x, tiles_y):
    palette_map = []
    palettes = []

    for y in range(tiles_y):
        for x in range(tiles_x):
            px, py = x*8, y*8
            td = data[px:px+8, py:py+8]
            td_dx = data_dx[px:px+8, py:py+8]

            pal = {}

            for ndi, ndv in zip(np.nditer(td), np.nditer(td_dx)):
                i = ndi.item(0)
                v = ndv.item(0)
                if i in pal:
                    if pal[i] != v:
                        raise ValueError("Overloaded colors in tile ({},{}).".format(x, y))
                else:
                    pal[i] = v

            index = -1
            for i in range(len(palette_map)):
                if all(k not in pal or pal[k] == v for k, v in palette_map[i].items()):
                    index = i
                    break

            if index == -1:
                index = len(palette_map)
                palette_map.append(pal)

            for k,v in pal.items():
                palette_map[index][k] = v
            palettes.append(index)

    palette_data = []
    for m in palette_map:
        for i in range(4):
            if i in m:
                palette_data.append(rgb_to_5bit(*colors[m[i]]))
            else:
                palette_data.append(0)

    return palettes, palette_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Image file.", type=str)
    parser.add_argument("outfile", help="Output file.", type=str)
    parser.add_argument("-C", "--cfile", help="Write data to C source file instead of in header.", type=str)
    parser.add_argument("-c", "--color", help="Game Boy Color mode.", action="store_true")
    parser.add_argument("-d", "--dx", help="Color mode reference. Produces DMG and CGB compatible data for \"DX\"-style games.", type=str)
    parser.add_argument("-m", "--map", help="Produce tile map.", action="store_true")
    parser.add_argument("--s8x16", help="Enable 8x16 sprite mode.", action="store_true")
    parser.add_argument("-r", "--rle", help="Compress data using RLE.", action="store_true")
    parser.add_argument("-O", "--offset", help="Tile map offset.", type=int, default=0)
    parser.add_argument("-P", "--palette_offset", help="Palette index offset.", type=int, default=0)
    args = parser.parse_args()

    source = png.Reader(args.infile)
    width, height, data_map, meta = source.read()

    if width % 8 != 0 or height % 8 != 0:
        raise ValueError("Image dimensions not divisible by 8.")
    if "palette" not in meta:
        raise ValueError("PNG image is not indexed.")
    if not args.color and len(meta["palette"]) > 4:
        raise ValueError("At most 4 colors are supported in non-color mode.")

    data = np.array(list(data_map)).transpose()

    tiles_x = width // 8
    tiles_y = height // 8

    palettes, palette_data = None, None

    if args.s8x16:
        tileorder = [(x // 2, y + x % 2) for y in range(0, tiles_y, 2) for x in range(tiles_x*2)]
    else:
        tileorder = [(x, y) for y in range(tiles_y) for x in range(tiles_x)]

    if args.color:
        palettes, palette_map = make_color_palettes(data, meta["palette"], tiles_x, tiles_y)
        tile_data = [convert_tile_color(data, palette_map[palettes[t[0]+t[1]*tiles_x]], t[0], t[1]) for t in tileorder]
        tile_data_length = len(tile_data)
        palette_data = []
        for m in palette_map:
            for i in range(4):
                if i < len(m):
                    palette_data.append(rgb_to_5bit(*meta["palette"][m[i]]))
                else:
                    palette_data.append(0)

    else:
        tile_data = [convert_tile(data, t[0], t[1]) for t in tileorder]
        tile_data_length = len(tile_data)

        if args.dx:
            source_dx = png.Reader(args.dx)
            width_dx, height_dx, data_map_dx, meta_dx = source_dx.read()

            if width_dx != width or height_dx != height:
                raise ValueError("Dimension of DX reference image does not match input.")
            if "palette" not in meta_dx:
                raise ValueError("DX reference PNG image is not indexed.")

            data_dx = np.array(list(data_map_dx)).transpose()

            palettes, palette_data = make_dx_palettes(data, data_dx, meta_dx["palette"], tiles_x, tiles_y)

    if palettes != None:
        palettes = [i + args.palette_offset for i in palettes]

    if args.map:
        tile_map = dict()
        tiles = []
        for tile in tile_data:
            if tile not in tile_map:
                tile_map[tile] = len(tile_map)
            tiles.append(tile_map[tile])

        tile_data = np.zeros(16 * len(tile_map), np.uint8)
        for k,v in tile_map.items():
            tile_data[(v*16):(v+1)*16] = k

        tiles = [i + args.offset for i in tiles]

        if args.cfile:
            export.write_map_c_source(args.cfile, args.outfile, tile_data, tiles, tiles_x, tiles_y, args.offset, palettes, palette_data, args.palette_offset, rle=args.rle)
        else:
            export.write_map_c_header(args.outfile, tile_data, tiles, tiles_x, tiles_y, args.offset, palettes, palette_data, args.palette_offset, rle=args.rle)

    else:
        tile_data = np.fromiter(itertools.chain.from_iterable(tile_data), np.uint8)
        if args.cfile:
            export.write_sprites_c_source(args.cfile, args.outfile, tile_data, palettes, palette_data, rle=args.rle)
        else:
            export.write_sprites_c_header(args.outfile, tile_data, palettes, palette_data, rle=args.rle)

if __name__ == "__main__":
    main()

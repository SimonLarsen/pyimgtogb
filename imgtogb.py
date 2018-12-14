import argparse
import png
import numpy as np
import itertools
import export

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

def rgb_to_5bit(r, g, b):
    r = round(r  / 255 * 31)
    g = round(g  / 255 * 31)
    b = round(b  / 255 * 31)
    val = r + (g << 5) + (b << 10)
    return val & 255, val >> 8

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
                palette_data.extend(rgb_to_5bit(*colors[m[i]]))
            else:
                palette_data.append(0)
                palette_data.append(0)

    return palettes, palette_data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Image file.", type=str)
    parser.add_argument("outfile", help="Output file.", type=str)
    parser.add_argument("-c", "--color", help="Game Boy Color mode.", action="store_true")
    parser.add_argument("-d", "--dx", help="Color mode reference. Produces DMG and CGB compatible data for \"DX\"-style games.", type=str)
    parser.add_argument("-m", "--map", help="Produce tile map.", action="store_true")
    parser.add_argument("--8x16", help="Enable 8x16 sprite mode.", action="store_true")
    parser.add_argument("-r", "--rle", help="Compress data using RLE.", action="store_true")
    parser.add_argument("-O", "--offset", help="Tile map offset.", type=int, default=0)
    args = parser.parse_args()

    source = png.Reader(args.infile)
    width, height, data_map, meta = source.read()

    if width % 8 != 0 or width % 8 != 0:
        raise ValueError("Image dimensions not divisible by 8.")
    if "palette" not in meta:
        raise ValueError("PNG image is not indexed.")
    if not args.color and len(meta["palette"]) > 4:
        raise ValueError("At most 4 colors are supported in non-color mode.")

    data = np.array(list(data_map)).transpose()

    tiles_x = round(width / 8)
    tiles_y = round(height / 8)
    tile_data = [convert_tile(data, tx, ty) for ty in range(tiles_y) for tx in range(tiles_x)]
    tile_data_length = len(tile_data)

    palettes, palette_data = [], []

    if args.dx:
        source_dx = png.Reader(args.dx)
        width_dx, height_dx, data_map_dx, meta_dx = source_dx.read()

        if width_dx != width or height_dx != height:
            raise ValueError("Dimension of DX reference image does not match input.")
        if "palette" not in meta_dx:
            raise ValueError("DX reference PNG image is not indexed.")

        data_dx = np.array(list(data_map_dx)).transpose()

        palettes, palette_data = make_dx_palettes(data, data_dx, meta_dx["palette"], tiles_x, tiles_y)

    if args.map:
        tile_map = dict()
        tiles = []
        for tile in tile_data:
            if tile not in tile_map:
                tile_map[tile] = len(tile_map)
            tiles.append(tile_map[tile])

        tile_data = np.zeros(16 * len(tile_map), np.uint16)
        for k,v in tile_map.items():
            tile_data[(v*16):(v+1)*16] = k

        for i in range(len(tiles)):
            tiles[i] = tiles[i] + args.offset

        export.write_map_c_header(args.outfile, tile_data, tiles, tiles_x, tiles_y, args.offset, palettes, palette_data, rle=args.rle)

    else:
        tile_data = np.fromiter(itertools.chain.from_iterable(tile_data), np.uint16)
        export.write_sprites_c_header(args.outfile, tile_data, palettes, palette_data, rle=args.rle)

if __name__ == "__main__":
    main()

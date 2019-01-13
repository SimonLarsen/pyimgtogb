import argparse
import png
import numpy as np
import export


def convert_tile(data, palette, x, y):
    m = {}
    for i in range(len(palette)):
        m[palette[i]] = i

    px, py = x*8, y*8
    td = data[px:px+8, py:py+8]

    out = []
    for iy in range(8):
        for ix in range(0, 8, 4):
            b0 = m[td[ix, iy]]
            b1 = m[td[ix+1, iy]]
            b2 = m[td[ix+1, iy]]
            b3 = m[td[ix+1, iy]]
            out.append(b0 + (b1 << 4))
            out.append(b2 + (b3 << 4))
    return tuple(out)


def palette_to_15bit(r, g, b, a):
    ri = round(r / 255 * 31)
    gi = round(g / 255 * 31)
    bi = round(b / 255 * 31)
    
    b0 = (ri + (gi << 5)) & 255
    b1 = (gi >> 5) + (bi << 2)
    return b0, b1


def consolidate_transparent(data, width, height, colors):
    trans = [i for i in range(len(colors)) if colors[i][3] < 255]

    if len(trans) == 0:
        colors.append((0, 0, 0, 0))

    for i in range(1, len(trans)):
        data[data == i] = trans[0]

    return data, colors


def make_palettes(data, width, height, colors):
    palette_map = []
    palettes = []

    tiles_x = width // 8
    tiles_y = height // 8

    trans = next(i for i in range(len(colors)) if colors[i][3] < 255)

    for y in range(tiles_y):
        for x in range(tiles_x):
            px, py = x*8, y*8
            td = data[px:px+8, py:py+8]
            values = np.unique(td)
            if len(values) > 16:
                raise ValueError("Tile ({},{}) contains more than 16 different colors.".format(x, y))

            index = -1
            for i in range(len(palette_map)):
                noverlap = sum(v in palette_map[i] for v in values)
                if len(palette_map[i]) + len(values) - noverlap <= 16:
                    index = i
                    break

            if index == -1:
                index = len(palette_map)
                palette_map.append([trans])

            for v in values:
                if v not in palette_map[index]:
                    palette_map[index].append(v)

            palettes.append(index)

    return palettes, palette_map


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Image file.", type=str)
    parser.add_argument("outfile", help="Output file.", type=str)
    args = parser.parse_args()

    source = png.Reader(args.infile)
    width, height, data_map, meta = source.read()

    tiles_x = width // 8
    tiles_y = height // 8

    data = np.array(list(data_map)).transpose()

    if width % 8 != 0 or height % 8 != 0:
        raise ValueError("Image dimensions not divisible by 8.")
    if "palette" not in meta:
        raise ValueError("PNG image is not indexed.")

    data, colors = consolidate_transparent(data, width, height, meta["palette"])
    palettes, palette_map = make_palettes(data, width, height, colors)
    tile_data = [convert_tile(data, palette_map[palettes[tx+ty*tiles_x]], tx, ty) for ty in range(tiles_y) for tx in range(tiles_x)]
    tile_data_length = len(tile_data)

    palette_data = []
    for m in palette_map:
        for i in range(16):
            if i < len(m):
                palette_data.extend(palette_to_15bit(*colors[m[i]]))
            else:
                palette_data.append(palette_to_15bit(0, 0, 0, 0))
    
    tile_map = dict()
    tiles = []
    for tile in tile_data:
        if tile not in tile_map:
            tile_map[tile] = len(tile_map)
        tiles.append(tile_map[tile])

    tile_data = np.zeros(32 * len(tile_map), np.uint8)
    for k,v in tile_map.items():
        tile_data[(v*32):(v+1)*32] = k

    export.write_border_c_header(args.outfile, tiles_x, tiles_y, tile_data, tiles, palettes, palette_data)


if __name__ == "__main__":
    main()

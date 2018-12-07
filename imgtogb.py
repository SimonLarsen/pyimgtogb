import os
import argparse
import png
import numpy as np
import itertools
from string import Template

RLE_MAX_RUN = 200

def convert_tile(data, x, y):
    px, py = x*8, y*8
    td = data[px:px+8, py:py+8]
    values = np.unique(td)
    values.sort()
    pmap = {values[i]: i for i in range(len(values))}

    out = []
    for iy in range(8):
        b0, b1 = 0, 0
        for ix in range(8):
            color = td[ix, iy]
            v = pmap[color]

            b0 |= (v & 1) << (7 - ix)
            b1 |= ((v & 2) >> 1) << (7 - ix)

        out.append(b0)
        out.append(b1)

    return tuple(out)


def compress_rle(data):
    value = data[0]
    run, i = 1, 1
    out = []
    while i < len(data):
        if data[i] == data[i-1] and run < RLE_MAX_RUN:
            run = run + 1
        else:
            out.append(data[i-1])
            if run > 1:
                out.append(data[i-1])
                out.append(run)
            run = 1
        i = i + 1

    out.append(data[-1])
    if run > 1:
        out.append(data[-1])
        out.append(run)

    return out


def write_sprites_c_header(path, tile_data, tile_data_length):
    name = os.path.splitext(os.path.basename(path))[0]
    temp = Template("""#ifndef ${uname}_SPRITES_H
#define ${uname}_SPRITES_H

#define ${name}_data_length $datalength
const unsigned char ${name}_data[] = {
    ${data}
};

#endif\n""")

    s_td = ",\n    ".join([", ".join(map(lambda x: str(x).rjust(3), tile_data[i:i+16])) for i in range(0, len(tile_data), 16)])

    s = temp.substitute(
        uname=name.upper(),
        name=name,
        datalength=tile_data_length,
        data=s_td
    )

    with open(path, "w") as f:
        f.write(s)


def write_map_c_header(path, tile_data, tile_data_length, tiles, tiles_width, tiles_height, tiles_offset):
    name = os.path.splitext(os.path.basename(path))[0]
    temp = Template("""#ifndef ${uname}_MAP_H
#define ${uname}_MAP_H

#define ${name}_data_length $length
const unsigned char ${name}_data[] = {
    ${data}
};

#define ${name}_tiles_width ${width}
#define ${name}_tiles_height ${height}
#define ${name}_tiles_offset ${offset}
const unsigned char ${name}_tiles[] = {
    ${tiles}
};

#endif\n""")

    s_td = ",\n    ".join([", ".join(map(lambda x: str(x).rjust(3), tile_data[i:i+16])) for i in range(0, len(tile_data), 16)])
    s_t = ",\n    ".join([", ".join(map(lambda x: str(x).rjust(3), tiles[i:i+16])) for i in range(0, len(tiles), 16)])

    s = temp.substitute(
        uname=name.upper(),
        name=name,
        length=tile_data_length,
        data=s_td,
        tiles=s_t,
        width=tiles_width,
        height=tiles_height,
        offset=tiles_offset
    )

    with open(path, "w") as f:
        f.write(s)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("infile", help="Image file.", type=str)
    parser.add_argument("outfile", help="Output file.", type=str)
    parser.add_argument("-m", "--map", help="Produce tile map.", action="store_true")
    parser.add_argument("--8x16", help="Enable 8x16 sprite mode.", action="store_true")
    parser.add_argument("-r", "--rle", help="Compress data using RLE.", action="store_true")
    parser.add_argument("-O", "--offset", help="Tile map offset.", type=int, default=0)
    args = parser.parse_args()

    source = png.Reader(args.infile)
    width, height, data_map, meta = source.read()

    if width % 8 != 0 or width % 8 != 0:
        raise ValueError("Image dimensions not divisible by 8.")

    tiles_x = round(width / 8)
    tiles_y = round(height / 8)

    data = np.array(list(data_map)).transpose()

    tile_data = [convert_tile(data, tx, ty) for ty in range(tiles_y) for tx in range(tiles_x)]
    tile_data_length = len(tile_data)

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

        if args.rle:
            tile_data = compress_rle(tile_data)
            tiles = compress_rle(tiles)

        for i in range(len(tiles)):
            tiles[i] = tiles[i] + args.offset

        write_map_c_header(args.outfile, tile_data, len(tile_map), tiles, tiles_x, tiles_y, args.offset)

    else:
        tile_data = np.fromiter(itertools.chain.from_iterable(tile_data), np.uint16)

        if args.rle:
            tile_data = compress_rle(tile_data)

        write_sprites_c_header(args.outfile, tile_data, tile_data_length)

if __name__ == "__main__":
    main()

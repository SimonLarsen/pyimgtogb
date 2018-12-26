import os
from string import Template
from rle import compress as rle_compress


def pretty_data(data):
    return ",\n    ".join([", ".join(map(lambda x: str(x).rjust(3), data[i:i+16])) for i in range(0, len(data), 16)])


def write_sprites_c_header(path, tile_data, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(path))[0]
    temp = Template("""#ifndef ${uname}_SPRITES_H
#define ${uname}_SPRITES_H
#define ${name}_data_length $datalength
const unsigned char ${name}_data[] = {
    ${data}
};
${palette_data}
#endif\n""")

    has_palettes = palettes != None

    tile_data_length = int(len(tile_data) / 16)
    palette_data_length = 0
    if has_palettes:
        palette_data_length = int(len(palette_data) / 4)

    if rle:
        tile_data = rle_compress(tile_data)
        if has_palettes:
            palettes = rle_compress(palettes)

    s_pal = ""
    if has_palettes:
        s_pal = Template("""
const unsigned char ${name}_palettes[] = {
    ${palettes}
};
#define ${name}_palette_data_length ${pdlen}
const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};""").substitute(name=name, pdlen=palette_data_length, palettes=pretty_data(palettes), palette_data=pretty_data(palette_data))

    s = temp.substitute(
        uname=name.upper(),
        name=name,
        datalength=tile_data_length,
        data=pretty_data(tile_data),
        palette_data=s_pal
    )

    with open(path, "w") as f:
        f.write(s)


def write_map_c_header(path, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes=None, palette_data=None, rle=False):
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
${palette_data}
#endif\n""")

    has_palettes = palettes != None

    tile_data_length = int(len(tile_data) / 16)
    palette_data_length = 0
    if has_palettes:
        palette_data_length = int(len(palette_data) / 4)

    if rle:
        tile_data = rle_compress(tile_data)
        tiles = rle_compress(tiles)
        if has_palettes:
            palettes = rle_compress(palettes)

    s_pal = ""
    if has_palettes:
        s_pal = Template("""
const unsigned char ${name}_palettes[] = {
    ${palettes}
};
#define ${name}_palette_data_length ${pdlen}
const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};""").substitute(
        name=name,
        pdlen=palette_data_length,
        palettes=pretty_data(palettes),
        palette_data=pretty_data(palette_data)
    )

    s = temp.substitute(
        uname=name.upper(),
        name=name,
        length=tile_data_length,
        data=pretty_data(tile_data),
        tiles=pretty_data(tiles),
        width=tiles_width,
        height=tiles_height,
        offset=tiles_offset,
        palette_data=s_pal
    )

    with open(path, "w") as f:
        f.write(s)

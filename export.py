import os
from string import Template
from rle import compress as rle_compress


def pretty_data(data):
    return ",\n    ".join([", ".join(map(lambda x: str(x).rjust(3), data[i:i+16])) for i in range(0, len(data), 16)])


def write_sprites_c_header(path, tile_data, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(path))[0]

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
        s_pal = Template("""const unsigned char ${name}_palettes[] = {
    ${palettes}
};
#define ${name}_palette_data_length ${pdlen}
const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};""").substitute(name=name, pdlen=palette_data_length, palettes=pretty_data(palettes), palette_data=pretty_data(palette_data))

    s = Template("""#ifndef ${uname}_SPRITES_H
#define ${uname}_SPRITES_H
#define ${name}_data_length $datalength
const unsigned char ${name}_data[] = {
    ${data}
};
${palette_data}
#endif\n""").substitute(
        uname=name.upper(),
        name=name,
        datalength=tile_data_length,
        data=pretty_data(tile_data),
        palette_data=s_pal
    )

    with open(path, "w") as f:
        f.write(s)

def write_sprites_c_source(cpath, hpath, tile_data, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(hpath))[0]

    has_palettes = palettes != None

    tile_data_length = int(len(tile_data) / 16)
    palette_data_length = 0
    if has_palettes:
        palette_data_length = int(len(palette_data) / 4)

    if rle:
        tile_data = rle_compress(tile_data)
        if has_palettes:
            palettes = rle_compress(palettes)

    palette_c = ""
    palette_h = ""
    if has_palettes:
        palette_c = Template("""const unsigned char ${name}_palettes[] = {
    ${palettes}
};
const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};""").substitute(name=name, palettes=pretty_data(palettes), palette_data=pretty_data(palette_data))

        palette_h = Template("""#define ${name}_palette_data_length ${pdlen}
extern const unsigned char ${name}_palettes[];
extern const unsigned int ${name}_palette_data[];""").substitute(name=name, pdlen=palette_data_length)

    cdata = Template("""const unsigned char ${name}_data[] = {
    ${data}
};
${palette_c}
""").substitute(
        name=name,
        data=pretty_data(tile_data),
        palette_c=palette_c
   )

    hdata = Template("""#ifndef ${uname}_SPRITES_H
#define ${uname}_SPRITES_H
#define ${name}_data_length $datalength
extern const unsigned char ${name}_data[];
${palette_h}
#endif\n""").substitute(
        uname=name.upper(),
        name=name,
        datalength=tile_data_length,
        palette_h=palette_h
    )

    with open(cpath, "w") as f:
        f.write(cdata)

    with open(hpath, "w") as f:
        f.write(hdata)


def write_map_c_header(path, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(path))[0]
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
        s_pal = Template("""const unsigned char ${name}_palettes[] = {
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

    s = Template("""#ifndef ${uname}_MAP_H
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
#endif\n""").substitute(
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


def write_map_c_source(cpath, hpath, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(hpath))[0]

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

    palette_c = ""
    palette_h = ""
    if has_palettes:
        palette_c = Template("""const unsigned char ${name}_palettes[] = {
    ${palettes}
};
const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};""").substitute(
        name=name,
        palettes=pretty_data(palettes),
        palette_data=pretty_data(palette_data)
    )

        palette_h = Template("""#define ${name}_palette_data_length ${pdlen}
extern const unsigned char ${name}_palettes[];
extern const unsigned int ${name}_palette_data[];""").substitute(
        name=name,
        pdlen=palette_data_length,
    )

    cdata = Template("""const unsigned char ${name}_data[] = {
    ${data}
};
const unsigned char ${name}_tiles[] = {
    ${tiles}
};
${palette_c}
#endif\n""").substitute(
        name=name,
        data=pretty_data(tile_data),
        tiles=pretty_data(tiles),
        palette_c=palette_c
    )

    hdata = Template("""#ifndef ${uname}_MAP_H
#define ${uname}_MAP_H
#define ${name}_data_length $length
extern const unsigned char ${name}_data[];
#define ${name}_tiles_width ${width}
#define ${name}_tiles_height ${height}
#define ${name}_tiles_offset ${offset}
extern const unsigned char ${name}_tiles[];
${palette_h}
#endif\n""").substitute(
        uname=name.upper(),
        name=name,
        length=tile_data_length,
        width=tiles_width,
        height=tiles_height,
        offset=tiles_offset,
        palette_h=palette_h
    )

    with open(cpath, "w") as f:
        f.write(cdata)

    with open(hpath, "w") as f:
        f.write(hdata)


def write_border_c_header(path, tiles_width, tiles_height, tile_data, tiles, palettes, palette_data):
    name = os.path.splitext(os.path.basename(path))[0]
    s = Template("""#ifndef ${uname}_BORDER_H
#define ${uname}_BORDER_H
#define ${name}_data_length $datalength
const unsigned char ${name}_data[] = {
    ${data}
};
#define ${name}_tiles_width ${width}
#define ${name}_tiles_height ${height}
const unsigned char ${name}_tiles[] = {
    ${tiles}
};
const unsigned char ${name}_palettes[] = {
    ${palettes}
};
#define ${name}_num_palettes $palettecount
const unsigned char ${name}_palette_data[] = {
    ${palettedata}
};
#endif\n""").substitute(
        uname=name.upper(),
        name=name,
        datalength=len(tile_data) // 32,
        data=pretty_data(tile_data),
        width=tiles_width,
        height=tiles_height,
        tiles=pretty_data(tiles),
        palettes=pretty_data(palettes),
        palettecount=len(palette_data) // 32,
        palettedata=pretty_data(palette_data)
    )

    with open(path, "w") as f:
        f.write(s)

import os
from string import Template
from rle import compress as rle_compress


def pretty_data(data, w=16):
    return ",\n    ".join([", ".join(map(lambda x: str(x).rjust(3), data[i:i+w])) for i in range(0, len(data), w)])


def gen_sprites_data(name, tile_data, palettes, palette_data, rle):
    has_palettes = palettes != None

    tile_data_length = int(len(tile_data) / 16)
    palette_data_length = 0
    if has_palettes:
        palette_data_length = int(len(palette_data) / 4)

    if rle:
        tile_data = rle_compress(tile_data)
        if has_palettes:
            palettes = rle_compress(palettes)

    pal_defs = ""
    pal_data = ""

    if has_palettes:
        pal_defs = Template("""#define ${name}_palette_data_length ${pdlen}""").substitute(
            name=name,
            pdlen=palette_data_length
        )

        pal_data = Template("""const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};
const unsigned char ${name}_palettes[] = {
    ${palettes}
};""").substitute(
            name=name,
            palette_data=pretty_data(palette_data, 4),
            palettes=pretty_data(palettes)
        )

    spr_defs = Template("""#define ${name}_data_length ${datalength}""").substitute(
        name=name,
        datalength=tile_data_length
    )

    spr_data = Template("""const unsigned char ${name}_data[] = {
    ${data}
};""").substitute(
        name=name,
        data=pretty_data(tile_data)
    )

    return spr_defs, spr_data, pal_defs, pal_data


def write_sprites_c_header(path, tile_data, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(path))[0]

    spr_defs, spr_data, pal_defs, pal_data = gen_sprites_data(name, tile_data, palettes, palette_data, rle)

    s = Template("""#ifndef ${uname}_SPRITES_H
#define ${uname}_SPRITES_H
${spr_defs}
${spr_data}
${pal_defs}
${pal_data}
#endif\n""").substitute(
        uname=name.upper(),
        spr_defs=spr_defs,
        spr_data=spr_data,
        pal_defs=pal_defs,
        pal_data=pal_data
    )

    with open(path, "w") as f:
        f.write(s)


def write_sprites_c_source(cpath, hpath, tile_data, palettes=None, palette_data=None, rle=False):
    name = os.path.splitext(os.path.basename(hpath))[0]

    spr_defs, spr_data, pal_defs, pal_data = gen_sprites_data(name, tile_data, palettes, palette_data, rle)

    has_palettes = palettes != None

    s_externs = "extern const unsigned char ${name}_data[];"

    if has_palettes:
        s_externs += """extern const unsigned char ${name}_palettes[];
extern const unsigned int ${name}_palette_data[];"""

    s_header = Template("""#ifndef ${uname}_SPRITES_H
#define ${uname}_SPRITES_H
${spr_defs}
${pal_defs}
${externs}
#endif""").substitute(
        uname=name.upper(),
        spr_defs=spr_defs,
        pal_defs=pal_defs,
        externs=Template(s_externs).substitute(name=name)
    )

    s_source = Template("""#include "${hpath}"
${spr_data}
${pal_data}""").substitute(
        hpath=hpath,
        spr_data=spr_data,
        pal_data=pal_data
    )

    with open(cpath, "w") as f:
        f.write(s_source)

    with open(hpath, "w") as f:
        f.write(s_header)


def gen_map_data(name, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes=None, palette_data=None, palette_offset=None, rle_data=False, rle_tiles=False):
    has_palettes = palettes != None

    tile_data_length = int(len(tile_data) / 16)
    palette_data_length = 0
    if has_palettes:
        palette_data_length = int(len(palette_data) / 4)

    if rle_data:
        tile_data = rle_compress(tile_data)
    if rle_tiles:
        tiles = rle_compress(tiles)
        if has_palettes:
            palettes = rle_compress(palettes)

    pal_defs = ""
    pal_data = ""

    if has_palettes:
        pal_defs = Template("""#define ${name}_palette_data_length ${pdlen}
#define ${name}_palette_offset ${paloffset}""").substitute(
            name=name,
            pdlen=palette_data_length,
            paloffset=palette_offset
        )

        pal_data = Template("""const unsigned char ${name}_palettes[] = {
    ${palettes}
};

const unsigned int ${name}_palette_data[] = {
    ${palette_data}
};""").substitute(
            name=name,
            palettes=pretty_data(palettes, 20),
            palette_data=pretty_data(palette_data, 4)
        )

    map_defs = Template("""#define ${name}_data_length $length
#define ${name}_tiles_width ${width}
#define ${name}_tiles_height ${height}
#define ${name}_tiles_offset ${offset}""").substitute(
        name=name,
        length=tile_data_length,
        width=tiles_width,
        height=tiles_height,
        offset=tiles_offset
    )

    map_data = Template("""const unsigned char ${name}_data[] = {
    ${data}
};

const unsigned char ${name}_tiles[] = {
    ${tiles}
};""").substitute(
        name=name,
        data=pretty_data(tile_data),
        tiles=pretty_data(tiles, 20)
    )

    return map_defs, map_data, pal_defs, pal_data

def write_map_c_header(path, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes=None, palette_data=None, palette_offset=None, rle_data=False, rle_tiles=False):
    name = os.path.splitext(os.path.basename(path))[0]

    map_defs, map_data, pal_defs, pal_data = gen_map_data(name, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes, palette_data, palette_offset, rle_data, rle_tiles)

    s = Template("""#ifndef ${uname}_MAP_H
#define ${uname}_MAP_H
${map_defs}
${map_data}
${pal_defs}
${pal_data}
#endif\n""").substitute(
        uname=name.upper(),
        map_defs=map_defs,
        map_data=map_data,
        pal_defs=pal_defs,
        pal_data=pal_data
    )

    with open(path, "w") as f:
        f.write(s)


def write_map_c_source(cpath, hpath, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes=None, palette_data=None, palette_offset=None, rle_data=False, rle_tiles=False):
    name = os.path.splitext(os.path.basename(hpath))[0]
    has_palettes = palettes != None

    map_defs, map_data, pal_defs, pal_data = gen_map_data(name, tile_data, tiles, tiles_width, tiles_height, tiles_offset, palettes, palette_data, palette_offset, rle_data, rle_tiles)

    s_externs = """
extern const unsigned char ${name}_data[];
extern const unsigned char ${name}_tiles[];"""

    if has_palettes:
        s_externs += """extern const unsigned char ${name}_palettes[];
extern const unsigned int ${name}_palette_data[];"""

    s_header = Template("""#ifndef ${uname}_MAP_H
#define ${uname}_MAP_H
${map_defs}
${pal_defs}
${externs}
#endif\n""").substitute(
        uname=name.upper(),
        map_defs=map_defs,
        pal_defs=pal_defs,
        externs=Template(s_externs).substitute(name=name)
    )

    s_source = Template("""#include "${hpath}"
${map_data}
${pal_data}\n""").substitute(
        hpath=hpath,
        map_data=map_data,
        pal_data=pal_data
    )

    with open(cpath, "w") as f:
        f.write(s_source)

    with open(hpath, "w") as f:
        f.write(s_header)


def write_border_c_header(path, tile_data, tiles, palettes, palette_data, rle=False):
    name = os.path.splitext(os.path.basename(path))[0]

    tile_data_length = len(tile_data) // 32
    palette_count = len(palette_data) // 16

    tile_data1 = tile_data[0:0x1000]
    tile_data2 = tile_data[0x1000:0x2000]

    if rle:
        tile_data1 = rle_compress(tile_data1)
        tile_data2 = rle_compress(tile_data2)
        tiles = rle_compress(tiles)
        palettes = rle_compress(palettes)

    s = Template("""#ifndef ${uname}_BORDER_H
#define ${uname}_BORDER_H
#define ${name}_data_length $datalength
const unsigned char ${name}_data1[] = {
    ${data1}
};
const unsigned char ${name}_data2[] = {
    ${data2}
};
const unsigned char ${name}_tiles[] = {
    ${tiles}
};
const unsigned char ${name}_palettes[] = {
    ${palettes}
};
#define ${name}_num_palettes $palettecount
const unsigned int ${name}_palette_data[] = {
    ${palettedata}
};
#endif\n""").substitute(
        uname=name.upper(),
        name=name,
        datalength=tile_data_length,
        data1=pretty_data(tile_data1),
        data2=pretty_data(tile_data2),
        tiles=pretty_data(tiles, 32),
        palettes=pretty_data(palettes, 32),
        palettecount=palette_count,
        palettedata=pretty_data(palette_data)
    )

    with open(path, "w") as f:
        f.write(s)

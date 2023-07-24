import copy

import pefile

from lxml.etree import parse as etree_parse
from lxml.builder import E

CHART_MASKS = [0x00080000, 0, 0x01000000, 0x02000000, 0, 0x04000000, None]


def is_placeholder_song(c):
    return c['fw_genre'] == c['fw_title'] == c['fw_artist'] == c['genre'] == c['title'] == c['artist'] == '‐'


def is_placeholder_chara(c):
    return c['flags'] & 3 != 0


def translate_konami_string(data):
    replace_str = [
        # ["鶉", "ó"],
        # ["鶇", "ö"],
        # ["圈", "é"],
        # ["鶫", "²"],
        # ["鵝", "7"],
        # ["囿", "♡"],
        # ["囂", "♡"],
        # ["鵑", ""],
        # ["鶚", "㊙"],
        # ["鵺", "Ü"],
        # ["圄", "à"],
        # ["圖", "ţ"],
        # ["鵤", "Ä"],
        # ["塔e", "∮テ"],
        # ["囎", ":"],
        # ["鵙", "ǝ"],
        # ["圉", "ä"],
    ]

    strdata = data.decode('cp932', errors="ignore").strip('\0')

    for c in replace_str:
        strdata = strdata.replace(c[0], c[1])

    return strdata


def calculate_struct_len(data_struct):
    return sum([data_struct[k][0] * data_struct[k][1] for k in data_struct])


def read_struct_data(pe, data_struct, data, index):
    data_struct_len = calculate_struct_len(data_struct)

    offset = index * data_struct_len

    output = {
        '_id': index,
        '_type': data_struct,
    }

    idx = 0
    for k in data_struct:
        dsize, dcount, is_ptr = data_struct[k][:3]

        if dcount > 1:
            output[k] = []

        for i in range(dcount):
            if 'string' in data_struct[k]:
                cur_data = translate_konami_string(data[offset+idx:offset+idx+dsize])
            else:
                cur_data = int.from_bytes(data[offset+idx:offset+idx+dsize], 'little', signed='signed' in data_struct[k])

            if 'ignore' in data_struct[k] and cur_data != 0:
                print(index)
                print("Field set to be ignored, but it has non-zero data")

                import hexdump
                hexdump.hexdump(data[offset:offset+data_struct_len])

                exit(1)

            if is_ptr:
                # Remove image base (0x10000000) from pointer address and get string data
                cur_data = translate_konami_string(pe.get_string_at_rva(rva=cur_data - 0x10000000))

            if dcount == 1:
                output[k] = cur_data

            else:
                output[k].append(cur_data)

            idx += dsize

        if 'ignore' in data_struct[k] or 'ignore_silent' in data_struct[k]:
            del output[k]

    return output


def get_type(struct, k):
    if 'charts' in struct[k]:
        return "charts"

    if 'string' in struct[k] or struct[k][2] == True:
        return "str"

    size = struct[k][0] * 8
    sign = "s" if 'signed' in struct[k] else "u"
    return "%s%d" % (sign, size)


def serialize_data_charts(x):
    output = []

    for chart_idx, chart in enumerate(x):
        if chart == 0:
            continue

        idx = chart.get('_idx', str(chart_idx))

        if '_idx' in chart:
            del chart['_idx']

        output.append(E('chart', *serialize_data(chart), idx=idx))

    return output

def serialize_data(x):
    ret = []

    for k in x:
        if k.startswith("_") or x[k] is None:
            continue

        if get_type(x['_type'], k) in ['charts']:
            ret.append(E(k, *serialize_data_charts(x[k])))

        elif type(x[k]) in [list, dict] and '_type' in x[k]:
            ret.append(E(k, *serialize_data(x[k])))

        elif type(x[k]) in [list]:
            ret.append(E(
                k,
                " ".join([str(v) for v in x[k]]) if type(x[k]) in [list] else str(x[k]),
                __type=get_type(x['_type'], k),
                __count=str(len(x[k]) if type(x[k]) in [list] else 1),
            ))

        else:
            ret.append(E(
                k,
                " ".join([str(v) for v in x[k]]) if type(x[k]) in [list] else str(x[k]),
                __type=get_type(x['_type'], k),
            ))

    return ret


def parse_database_from_dll(input_dll_filename, input_patch_xml_filename):
    # Format: [size, num, ptr_flag]
    data_struct_song = {
        'fw_genre': [4, 1, True],
        'fw_title': [4, 1, True],
        'fw_artist': [4, 1, True],
        'genre': [4, 1, True],
        'title': [4, 1, True],
        'artist': [4, 1, True],
        'chara1': [2, 1, False],
        'chara2': [2, 1, False],
        'mask': [4, 1, False],
        'folder': [4, 1, False],
        'cs_version': [4, 1, False],
        'categories': [4, 1, False],
        'diffs': [1, 6, False],
        'charts': [2, 7, False, 'charts'],
        'ha': [4, 1, True],
        'chara_x': [4, 1, False], # Hariai positioning it seems
        'chara_y': [4, 1, False], # Hariai positioning it seems
        'unk1': [2, 32, False],
        'display_bpm': [2, 12, False],
        'hold_flags': [1, 8, False],
    }

    data_struct_file = {
        'folder': [4, 1, True],
        'filename': [4, 1, True],
        'audio_param1': [4, 1, False, 'signed'], # Something relating to volume/pan/etc?
        'audio_param2': [4, 1, False, 'signed'], # Something relating to volume/pan/etc?
        'audio_param3': [4, 1, False, 'signed'], # Something relating to volume/pan/etc?
        'audio_param4': [4, 1, False, 'signed'], # Something relating to volume/pan/etc?
        'file_type': [4, 1, False], # <= 0 is shiri.ifs, <= 5 is shiri_%d.ifs, anything else is shiri_diff.ifs
        'used_keys': [2, 1, False], # Bit field that says what notes were used in the chart
        'pad': [2, 1, False, 'ignore'],
    }

    data_struct_chara = {
        'chara_id': [4, 1, True],
        'flags': [4, 1, False], # Controls visibility, etc. bit 1 = C_DEL, bit 2 = CPU-only, bit 5 = disabled/off?
        'folder': [4, 1, True],
        'gg': [4, 1, True],
        'cs': [4, 1, True],
        'icon1': [4, 1, True],
        'icon2': [4, 1, True],
        'chara_xw': [2, 1, False], # Some kind of width or x position. If mask in data_struct_song has bit 23 (0x800000) set then this is ignored
        'chara_yh': [2, 1, False], # Some kind of height or y position. If mask in data_struct_song has bit 23 (0x800000) set then this is ignored
        'display_flags': [4, 1, False], # Some kind of bitfield flags.
            # If bit 1 is set then linear = 1
            # If bit 0 is not set then copy (flags2 & 2) into the linear flag field (doesn't have any effect?)
            # If bit 6 (0x20) is set then clipping = 1
            # If bit 6 (0x20) is not set then copy (flags & 0x10) >> 3 into the clipping flag field
            # Bit 8 (0x100) is unused?? Is set for gg_mimi_15a
        'flavor': [2, 1, False, 'signed'],
        'chara_variation_num': [1, 1, False],
        'pad': [1, 1, False, 'ignore'],
        'sort_name': [4, 1, True],
        'disp_name': [4, 1, True],
        'file_type': [4, 1, False], # <= 0 is shiri.ifs, <= 5 is shiri_%d.ifs, anything else is shiri_diff.ifs
        'lapis_shape': [4, 1, False], # non/dia/tear/heart/squ
        'lapis_color': [1, 1, False], # non/blue/pink/red/green/normal/yellow/purple/black
        'pad2': [1, 3, False, 'ignore'],
        'ha': [4, 1, True],
        'catchtext': [4, 1, True],
        'win2_trigger': [2, 1, False, 'signed'], # If played against a specific character ID, it triggers a win 2 animation
        'pad3': [1, 2, False, 'ignore'],
        'game_version': [4, 1, False], # What version this particular style was introduced
    }

    data_struct_flavors = {
        'phrase1': [13, 1, False, 'string'],
        'phrase2': [13, 1, False, 'string'],
        'phrase3': [13, 1, False, 'string'],
        'phrase4': [13, 1, False, 'string'],
        'phrase5': [13, 1, False, 'string'],
        'phrase6': [13, 1, False, 'string'],
        'pad': [2, 1, False, 'ignore'],
        'birthday': [4, 1, True],
        'chara1_birth_month': [1, 1, False],
        'chara2_birth_month': [1, 1, False],
        'chara3_birth_month': [1, 1, False],
        'chara1_birth_date': [1, 1, False],
        'chara2_birth_date': [1, 1, False],
        'chara3_birth_date': [1, 1, False],
        'style1': [2, 1, False], # Font and other related stylings
        'style2': [2, 1, False], # Font and other related stylings
        'style3': [2, 1, False], # Font and other related stylings
    }

    data_struct_fontstyle = {
        'fontface': [4, 1, False],
        'color': [4, 1, False],
        'height': [4, 1, False],
        'width': [4, 1, False],
    }

    # Read XML file
    patch_xml = etree_parse(input_patch_xml_filename)
    music_db_limit = patch_xml.find('limits').find('music').text
    music_db_limit = int(music_db_limit, 16 if music_db_limit.startswith("0x") else 10)

    chart_table_limit = patch_xml.find('limits').find('chart').text
    chart_table_limit = int(chart_table_limit, 16 if chart_table_limit.startswith("0x") else 10)

    style_table_limit = patch_xml.find('limits').find('style').text
    style_table_limit = int(style_table_limit, 16 if style_table_limit.startswith("0x") else 10)

    flavor_table_limit = patch_xml.find('limits').find('flavor').text
    flavor_table_limit = int(flavor_table_limit, 16 if flavor_table_limit.startswith("0x") else 10)

    chara_table_limit = patch_xml.find('limits').find('chara').text
    chara_table_limit = int(chara_table_limit, 16 if chara_table_limit.startswith("0x") else 10)

    music_db_addr = int(patch_xml.find('buffer_base_addrs').find('music').text, 16)
    chart_table_addr = int(patch_xml.find('buffer_base_addrs').find('chart').text, 16)
    style_table_addr = int(patch_xml.find('buffer_base_addrs').find('style').text, 16)
    flavor_table_addr = int(patch_xml.find('buffer_base_addrs').find('flavor').text, 16)
    chara_table_addr = int(patch_xml.find('buffer_base_addrs').find('chara').text, 16)

    # Modified an old one off script for this so I don't feel like refactoring it too much to get rid of these
    music_db_end_addr = (music_db_limit) * calculate_struct_len(data_struct_song) + music_db_addr
    chart_table_end_addr = (chart_table_limit) * calculate_struct_len(data_struct_file) + chart_table_addr
    style_table_end_addr = (style_table_limit) * calculate_struct_len(data_struct_fontstyle) + style_table_addr
    flavor_table_end_addr = (flavor_table_limit) * calculate_struct_len(data_struct_flavors) + flavor_table_addr
    chara_table_end_addr = (chara_table_limit) * calculate_struct_len(data_struct_chara) + chara_table_addr

    pe = pefile.PE(input_dll_filename, fast_load=True)

    # Read font style table
    data = pe.get_data(style_table_addr - 0x10000000, style_table_end_addr - style_table_addr)
    fontstyle_table = [read_struct_data(pe, data_struct_fontstyle, data, i) for i in range(len(data) // calculate_struct_len(data_struct_fontstyle))]

    # Read flavor table
    data = pe.get_data(flavor_table_addr - 0x10000000, flavor_table_end_addr - flavor_table_addr)
    flavor_table = [read_struct_data(pe, data_struct_flavors, data, i) for i in range(len(data) // calculate_struct_len(data_struct_flavors))]

    for c in flavor_table:
        if c['style2'] == 0:
            c['style2'] = None

        elif c['style2'] - 11 >= 0:
            c['style2'] = fontstyle_table[c['style2'] - 11]

    # Read chara table
    data = pe.get_data(chara_table_addr - 0x10000000, chara_table_end_addr - chara_table_addr)
    charadb = [read_struct_data(pe, data_struct_chara, data, i) for i in range(len(data) // calculate_struct_len(data_struct_chara))]

    data_struct_chara['lapis_shape'].append('string')
    data_struct_chara['lapis_color'].append('string')
    flavors = []
    for c in charadb:
        c['lapis_shape'] = ["", "dia", "tear", "heart", "squ"][c['lapis_shape']]
        c['lapis_color'] = ["", "blue", "pink", "red", "green", "normal", "yellow", "purple", "black"][c['lapis_color']]
        flavors.append(c['flavor'])
        c['flavor'] = flavor_table[c['flavor']] if c['flavor'] >= 0 else None

    # Read chart/file table
    data = pe.get_data(chart_table_addr - 0x10000000, chart_table_end_addr - chart_table_addr)
    file_lookup = [read_struct_data(pe, data_struct_file, data, i) for i in range(len(data) // calculate_struct_len(data_struct_file))]

    # Read music database
    data = pe.get_data(music_db_addr - 0x10000000, music_db_end_addr - music_db_addr)
    musicdb = [read_struct_data(pe, data_struct_song, data, i) for i in range(len(data) // calculate_struct_len(data_struct_song))]

    # Add connections to other tables
    data_struct_song['chara1'].append('string')
    data_struct_song['chara2'].append('string')
    for c in musicdb:
        c['_type'] = copy.deepcopy(c['_type'])

        if not is_placeholder_song(c):
            charts = []

            for chart_idx, idx in enumerate(c['charts']):
                if CHART_MASKS[chart_idx] is not None and (CHART_MASKS[chart_idx] == 0 or c['mask'] & CHART_MASKS[chart_idx] != 0):
                    charts.append(copy.deepcopy(file_lookup[idx]))
                    charts[-1]['_type'] = copy.deepcopy(charts[-1]['_type'])
                    charts[-1]['_type']['diff'] = [1, 1, False]
                    charts[-1]['_type']['hold_flag'] = [1, 1, False]

                    charts[-1]['diff'] = c['diffs'][chart_idx]
                    charts[-1]['_id'] = chart_idx
                    charts[-1]['_idx'] = ['ep', 'np', 'hp', 'op', 'bp_n', 'bp_h'][chart_idx]
                    charts[-1]['hold_flag'] = c['hold_flags'][chart_idx]

                else:
                    charts.append(0)

            c['charts'] = charts

        # Remove chart mask flags because they'll be added later in popnmusichax based on the charts available
        mask_full = sum([x for x in CHART_MASKS if x is not None])
        c['mask'] = c['mask'] & ~mask_full

        for k in ['diffs', 'hold_flags']:
            if k in c['_type']:
                del c['_type'][k]

            if k in c:
                del c[k]

        c['chara1'] = charadb[c['chara1']]['chara_id'] if c['chara1'] != 0 else 0
        c['chara2'] = charadb[c['chara2']]['chara_id'] if c['chara2'] != 0 else 0

    database = {
        'musicdb': musicdb,
        'charadb': charadb
    }

    return database

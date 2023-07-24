import argparse
import os
import sys

import ifstools

import popndll

from enum import Enum

from lxml.etree import tostring, fromstring
from lxml.builder import E


class DataErrors(Enum):
    SD_PATH_NOT_EXIST = 1
    SD_IFS_NOT_EXIST = 2
    SD_CHARTS_NOT_FOUND = 3
    SD_CHARTS_UNUSED = 4
    KC_NOT_FOUND = 5
    BG_NOT_FOUND = 6
    CHARA_IFS_NOT_FOUND = 7
    CHARA_IFS_INNER_NOT_FOUND = 8
    IFS_READ_ERROR = 9
    SD_CHART_ERROR = 10


CHART_LABELS = ["ep", "np", "hp", "op", "bp", "bp"]
CHART_MASKS = [0x00080000, 0, 0x01000000, 0x02000000, 0, 0x04000000]


def elem2dict(node):
    """
    Convert an lxml.etree node tree into a dict.
    Source: https://gist.github.com/jacobian/795571#gistcomment-2810160
    """
    result = {}

    idx = node.get('id', None)
    if idx:
        result['_id'] = int(idx)

    idx = node.get('idx', None)
    if idx:
        labels = ["ep", "np", "hp", "op", "bp_n", "bp_h"]

        if idx in labels:
            idx = labels.index(idx)

        result['_id'] = int(idx)

    for element in node.iterchildren():
        # Remove namespace prefix
        key = element.tag.split('}')[1] if '}' in element.tag else element.tag

        if key == 'charts':
            value = [0] * 7

            for chart in element.iterchildren():
                chart_data = elem2dict(chart)
                value[chart_data['_id']] = chart_data

        else:
            # Process element as tree element if the inner XML contains non-whitespace content
            if element.text and element.text.strip():
                elm_type = element.get('__type', None)
                elm_count = element.get('__count', None)

                value = element.text

                if elm_count:
                    value = value.split(' ')

                if elm_type in ['u8', 's8', 'u16', 's16', 'u32', 's32']:
                    if type(value) is list:
                        value = [int(x) for x in value]

                    else:
                        value = int(value)

            else:
                value = elem2dict(element)

        result[key] = value

    return result


def convert_db_to_dict(db):
    return {i: entry for i, entry in enumerate(db)}


def load_patch_dbs(input_db_folder, databases):
    def get_sequential_files(db, master_xml_path, target_elm):
        master_xml = fromstring(open(master_xml_path, "rb").read().replace(b"shift-jis", b"cp932"))

        for filename in master_xml.findall('filename'):
            patch_xml = fromstring(open(os.path.join(input_db_folder, filename.text), "rb").read().replace(b"shift-jis", b"cp932"))

            for elm in patch_xml.findall(target_elm):
                idx = int(elm.get('id'))

                new_entry = elem2dict(elm)

                if idx not in db:
                    db[idx] = new_entry

                else:
                    if 'charts' in db[idx]:
                        for chart in new_entry.get('charts', []):
                            if chart == 0:
                                continue

                            if db[idx]['charts'][chart['_id']] == 0:
                                db[idx]['charts'][chart['_id']] = chart

                            else:
                                db[idx]['charts'][chart['_id']].update(chart)

                    if 'charts' in new_entry:
                        del new_entry['charts']

                    db[idx].update(new_entry)

        return db

    master_xml_path = os.path.join(input_db_folder, "master.xml")
    if not os.path.exists(master_xml_path):
        return databases

    databases['charadb'] = get_sequential_files(databases['charadb'], master_xml_path, "chara")
    databases['musicdb'] = get_sequential_files(databases['musicdb'], master_xml_path, "music")

    return databases


def verify_chart(data):
    assert(len(data) > 0)

    event_size = 12
    if len(data) / 12 != len(data) // 12:
        # The chart data should be divisble both as a float and int and get the same result
        event_size = 8

    elif len(data) / 8 != len(data) // 8:
        # The chart data should be divisble both as a float and int and get the same result
        event_size = 12

    else:
        # You can still get cases where the above check is true for 8 byte events so do more checking
        marker_8 = sorted(list(set([data[i+4] for i in range(0, len(data), 8)])))
        marker_12 = sorted(list(set([data[i+4] for i in range(0, len(data), 12)])))

        marker_8_diff = list(set(marker_8) - set([0x00, 0x45]))
        marker_12_diff = list(set(marker_12) - set([0x00, 0x45]))

        if len(marker_8_diff) > 0 and len(marker_12_diff) == 0:
            event_size = 12

        elif len(marker_8_diff) == 0 and len(marker_12_diff) > 0:
            event_size = 8

        elif len(marker_8_diff) == 0 and len(marker_12_diff) == 0:
            # Inconclusive, do more testing
            cmd_8 = sorted(list(set([data[i+5] for i in range(0, len(data), 8)])))
            cmd_12 = sorted(list(set([data[i+5] for i in range(0, len(data), 12)])))

            cmd_8_diff = list(set(cmd_8) - set([1, 2, 3, 4, 5, 6, 7, 8, 10, 11]))
            cmd_12_diff = list(set(cmd_12) - set([1, 2, 3, 4, 5, 6, 7, 8, 10, 11]))

            if len(cmd_8_diff) > 0 and len(cmd_12_diff) == 0:
                event_size = 12

            elif len(cmd_8_diff) == 0 and len(cmd_12_diff) > 0:
                event_size = 8

            else:
                raise Exception("Couldn't determine size of chart events")

    events_by_cmd = {}
    events = []
    for i in range(0, len(data), event_size):
        chunk = data[i:i+event_size]

        if len(chunk) != event_size:
            break

        timestamp = int.from_bytes(chunk[:4], 'little')
        marker = chunk[4]
        cmd = chunk[5] & 0x0f
        param1 = chunk[5] >> 4
        param2 = chunk[6:8]
        param3 = chunk[8:] if event_size == 12 else 0

        # import hexdump
        # hexdump.hexdump(chunk)

        event = (chunk, timestamp, marker, cmd, param1, param2, param3)
        events.append(event)

        # is_valid_marker = (cmd in [0x0a, 0x0b] and marker == 0) or (cmd not in [0x0a, 0x0b] and marker == 0x45)
        # assert(is_valid_marker == True)

        if cmd not in events_by_cmd:
            events_by_cmd[cmd] = []

        events_by_cmd[cmd].append(event)

    chart_is_sequential = events == sorted(events, key=lambda x:x[1])
    assert(chart_is_sequential == True)

    chart_has_timings = 0x08 in events_by_cmd and len(events_by_cmd.get(0x08, [])) >= 6
    assert(chart_has_timings == True)

    chart_has_timings_at_zero = 0x08 in events_by_cmd and min([x[1] for x in events_by_cmd.get(0x08, [])]) == 0
    assert(chart_has_timings_at_zero == True)

    chart_timings = {x[5][1] >> 4: (x[5][1] & 0x0f) | x[5][0] for x in events_by_cmd.get(0x08, [])}
    chart_has_sequential_timings = sorted([chart_timings[k] for k in range(6)]) == [chart_timings[k] for k in range(6)]
    assert(chart_has_sequential_timings == True)

    standard_timings = [
        0x76, # Early bad
        0x7a, # Early good
        0x7e, # Early great
        0x84, # Late great
        0x88, # Late good
        0x8c, # Late bad
    ]
    chart_has_sensible_timings = [abs(chart_timings[k] - standard_timings[k]) < 15 for k in range(6)]
    chart_has_sensible_timings = list(set(chart_has_sensible_timings)) == [True]
    assert(chart_has_sensible_timings == True)

    chart_has_bpm = 0x04 in events_by_cmd and len(events_by_cmd.get(0x04, [])) > 0
    assert(chart_has_bpm == True)

    chart_has_bpm_at_zero = 0x04 in events_by_cmd and min([x[1] for x in events_by_cmd.get(0x04, [])]) == 0
    assert(chart_has_bpm_at_zero == True)

    chart_has_valid_bpms = 0x04 in events_by_cmd and min([int.from_bytes(x[5], 'little') for x in events_by_cmd.get(0x04, [])]) >= 0
    assert(chart_has_valid_bpms == True)

    chart_has_metronome = 0x05 in events_by_cmd and len(events_by_cmd.get(0x05, [])) > 0
    assert(chart_has_metronome == True)

    chart_has_metronome_at_zero = 0x05 in events_by_cmd and min([x[1] for x in events_by_cmd.get(0x05, [])]) == 0
    assert(chart_has_metronome_at_zero == True)

    used_notes = sorted(list(set([x[5][0] for x in events_by_cmd.get(0x01, [])])))
    is_valid_range_notes = not used_notes or (min(used_notes) >= 0 and max(used_notes) <= 8)
    assert(is_valid_range_notes == True)

    chart_has_notes = len(used_notes) > 0
    assert(chart_has_notes == True)

    used_notes = sorted(list(set([x[5][1] >> 4 for x in events_by_cmd.get(0x02, [])])))
    is_valid_range_keysound_range = not used_notes or (min(used_notes) >= 0 and max(used_notes) <= 8)
    assert(is_valid_range_notes == True)

    chart_has_keysounds = len(used_notes) > 0
    assert(chart_has_keysounds == True)

    used_notes = sorted(list(set([x[5][1] >> 4 for x in events_by_cmd.get(0x07, [])])))
    is_valid_range_auto_keysound_range = not used_notes or (min(used_notes) >= 0 and max(used_notes) <= 15)
    assert(is_valid_range_auto_keysound_range == True)

    chart_has_measures = len(events_by_cmd.get(0x0a, [])) > 0
    assert(chart_has_measures == True)

    chart_has_beats = len(events_by_cmd.get(0x0b, [])) > 0
    assert(chart_has_beats == True)

    chart_has_bgm_start = len(events_by_cmd.get(0x03, [])) > 0
    assert(chart_has_bgm_start == True)

    chart_has_single_bgm_start = len(events_by_cmd.get(0x03, [])) == 1
    assert(chart_has_single_bgm_start == True)

    chart_has_ending = len(events_by_cmd.get(0x06, [])) > 0
    assert(chart_has_ending == True)

    # chart_has_single_ending = len(events_by_cmd.get(0x06, [])) == 1
    # assert(chart_has_single_ending == True)

    if event_size == 12:
        hold_events = [(x[5][0], x[1], x[1] + int.from_bytes(x[6], 'little'), x[0]) for x in events_by_cmd.get(0x01, []) if int.from_bytes(x[6], 'little') > 0]

        for hold_event in hold_events:
            for x in events_by_cmd.get(0x01, []):
                if x[5][0] == hold_event[0] and x[1] != hold_event[1]:
                    is_impossible_hold = x[1] >= hold_event[1] and x[1] < hold_event[2]
                    assert(is_impossible_hold == False)

    chart_has_no_notes_at_zero = len([x for x in events_by_cmd.get(0x01, []) if x[1] == 0]) == 0
    assert(chart_has_no_notes_at_zero == True)

    return True


def verify_musicdb(musicdb, input_data_folder, is_mod_ifs):
    errors = []

    sd_path = os.path.join(input_data_folder, "sd")

    bg_ifs_path = os.path.join(input_data_folder, "tex", "system", "bg_mod.ifs" if is_mod_ifs else "bg_diff.ifs")
    bg_ifs = ifstools.IFS(bg_ifs_path)
    bg_ifs_files = [str(x) for x in bg_ifs.tree.all_files]
    bg_ifs.close()

    kc_ifs_path = os.path.join(input_data_folder, "tex", "system", "kc_mod.ifs" if is_mod_ifs else "kc_diff.ifs")
    kc_ifs = ifstools.IFS(kc_ifs_path)
    kc_ifs_files = [str(x) for x in kc_ifs.tree.all_files]
    kc_ifs.close()

    for music_idx in musicdb:
        entry = musicdb[music_idx]

        if popndll.is_placeholder_song(entry):
            # Skip placeholder entries
            continue

        # Generate mask and expected charts list
        if 'mask' not in entry:
            entry['mask'] = 0

        expected_charts = []
        for chart in entry.get('charts', []):
            if chart == 0:
                continue

            entry['mask'] |= CHART_MASKS[chart['_id']]

            if chart.get('diff', 0) == 0:
                # If a song has a 0 difficulty level then the game won't make it selectable so it doesn't matter if it exists or not
                continue

            if CHART_LABELS[chart['_id']] not in expected_charts:
                expected_charts.append(CHART_LABELS[chart['_id']])

        found_charts = []
        found_chart_errors = []
        for chart_idx, chart in enumerate(entry['charts']):
            if type(chart) is int:
                # Doesn't exist
                continue

            sd_game_path = os.path.join(sd_path, chart['folder'])
            if not os.path.exists(sd_game_path):
                print("Could not find", sd_game_path)
                errors.append((DataErrors.SD_PATH_NOT_EXIST, music_idx, [sd_game_path]))

            sd_ifs_base_path = os.path.join(sd_path, chart['folder'], chart['filename'])

            if chart['file_type'] > 0 and chart['file_type'] <= 5:
                sd_ifs_base_path = "%s_%02d" % (sd_ifs_base_path, chart['file_type'])

            elif chart['file_type'] > 0 and chart['file_type'] > 5:
                sd_ifs_base_path = "%s_diff" % (sd_ifs_base_path)

            sd_ifs_path = "%s.ifs" % (sd_ifs_base_path)

            if not os.path.exists(sd_ifs_path):
                print("Could not find", sd_ifs_path)
                errors.append((DataErrors.SD_IFS_NOT_EXIST, music_idx, [sd_ifs_path]))
                continue

            preview_filename = "%s_pre.2dx" % (chart['filename'])
            keysounds_filename = "%s.2dx" % (chart['filename'])

            target_chart_filename = "%s_%s.bin" % (chart['filename'], CHART_LABELS[chart_idx])

            ifs = ifstools.IFS(sd_ifs_path)
            found_preview = False
            found_keysounds = False
            found_target_chart = False
            for inner_filename in ifs.tree.all_files:
                found_preview = inner_filename == preview_filename or found_preview
                found_keysounds = inner_filename == keysounds_filename or found_keysounds
                found_target_chart = inner_filename == target_chart_filename or found_target_chart

                for chart_label in CHART_LABELS:
                    if str(inner_filename).endswith("_%s.bin" % chart_label):
                        found_charts.append(chart_label)

                        try:
                            verify_chart(inner_filename.load())

                        except BaseException as e:
                            import traceback
                            exc_type, exc_value, exc_traceback = sys.exc_info()
                            traceback_info = traceback.extract_tb(exc_traceback)
                            filename, line, func, text = traceback_info[-1]
                            errors.append((DataErrors.SD_CHART_ERROR, music_idx, [str(inner_filename), text]))
                            print(errors[-1])

            ifs.close()

        found_charts = list(set(found_charts))

        # TODO: Add check to make sure battle hyper chart exists?

        unused_charts = list(set(found_charts) - set(expected_charts))
        found_charts = list(set(found_charts) - set(unused_charts))
        found_charts = sorted(found_charts)
        expected_charts = sorted(expected_charts)

        if len(unused_charts) > 0:
            # print("Found unused charts:", found_charts, expected_charts, unused_charts)
            # errors.append((DataErrors.SD_CHARTS_UNUSED, music_idx, [found_charts, expected_charts, unused_charts]))
            pass

        if found_charts != expected_charts:
            errors.append((DataErrors.SD_CHARTS_NOT_FOUND, music_idx, [found_charts, expected_charts, list(set(expected_charts) - set(found_charts))]))

        kc_path = "kc_%04d.ifs" % (music_idx)
        if kc_path not in kc_ifs_files:
            errors.append((DataErrors.KC_NOT_FOUND, music_idx, [kc_path]))

        if entry.get('folder', 0) <= 21:
            # Later games don't use bg_*.ifs
            bg_path = "bg_%04d.ifs" % (music_idx)
            if bg_path not in bg_ifs_files:
                errors.append((DataErrors.BG_NOT_FOUND, music_idx, [bg_path]))

    return errors


def verify_charadb(charadb, input_data_folder, is_mod_ifs):
    errors = []

    tex_path = os.path.join(input_data_folder, "tex")

    for chara_idx in charadb:
        entry = charadb[chara_idx]

        if popndll.is_placeholder_chara(entry):
            # Skip placeholder entries
            continue

        chara_ifs_base_path = os.path.join(tex_path, entry['folder'], entry['chara_id'])

        if entry['file_type'] > 0 and entry['file_type'] <= 5:
            chara_ifs_base_path = "%s_%02d" % (chara_ifs_base_path, entry['file_type'])

        elif entry['file_type'] > 0 and entry['file_type'] > 5:
            chara_ifs_base_path = "%s_diff" % (chara_ifs_base_path)

        chara_ifs_path = "%s.ifs" % (chara_ifs_base_path)

        if not os.path.exists(chara_ifs_path):
            print("chara ifs not found:", chara_ifs_path)
            errors.append((DataErrors.CHARA_IFS_NOT_FOUND, chara_idx, [chara_ifs_path]))
            exit(1)

        try:
            chara_ifs = ifstools.IFS(chara_ifs_path)
            chara_ifs_files = [str(x) for x in chara_ifs.tree.all_files]

            icon1_path = os.path.join("tex", entry['icon1']) + ".png"
            icon2_path = os.path.join("tex", entry['icon2']) + ".png"
            gg_path = os.path.join("tex", entry['gg']) + ".png"

            for inner_path in [icon1_path, icon2_path, gg_path]:
                if inner_path not in chara_ifs_files:
                    print("chara inner file not found:", inner_path)
                    errors.append((DataErrors.CHARA_IFS_INNER_NOT_FOUND, chara_idx, [inner_path]))
                    exit(1)

        except:
            print("ifs read error:", chara_ifs_path)
            errors.append((DataErrors.IFS_READ_ERROR, chara_idx, [chara_ifs_path]))


        chara_ifs.close()

    return errors


def verify_data(databases, input_data_folder, is_mod_ifs):
    musicdb_errors = verify_musicdb(databases['musicdb'], input_data_folder, is_mod_ifs)
    charadb_errors = verify_charadb(databases['charadb'], input_data_folder, is_mod_ifs)

    for error in musicdb_errors + charadb_errors:
        print(error)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-dll', help='Input DLL file', default=None, required=True)
    parser.add_argument('--input-xml', help='Input XML file', default=None, required=True)
    parser.add_argument('--input-data', help='Input data folder', default=None, required=True)
    parser.add_argument('--input-db', help='Input db folder', default=None)

    args = parser.parse_args()

    databases = popndll.parse_database_from_dll(args.input_dll, args.input_xml)
    databases = {k: convert_db_to_dict(databases[k]) for k in databases}

    if args.input_db:
        databases = load_patch_dbs(args.input_db, databases)

    verify_data(databases, args.input_data, args.input_db is not None)
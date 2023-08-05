import argparse
import copy
import glob
import itertools
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile

import pydub

from bmx2bmson import bms2bmson

from PIL import Image
from lxml.etree import tostring, fromstring, XMLParser, parse as etree_parse
from lxml.builder import E

on_wsl = "microsoft" in platform.uname()[3].lower()

def insensitive_glob(pattern):
    def either(c):
        return '[%s%s]' % (c.lower(), c.upper()) if c.isalpha() else c
    return glob.glob(''.join(map(either, pattern)))


def calculate_timestamps(bmson, note_y):
    timestamp_at_y = {
        0: 0,
    }

    # Calculate timestamps based on pulses
    cur_bpm = bmson['info']['init_bpm']
    cur_bpm_pulse = 0

    new_timestamps = []

    last_event = None
    for bpm_event in bmson['bpm_events']:
        last_y = 0 if not last_event else last_event['y']
        last_bpm = bmson['info']['init_bpm'] if not last_event else last_event['v']
        time_per_pulse = ((60 / last_bpm) * 4) / 960
        timestamp_at_y[bpm_event['y']] = timestamp_at_y[last_y] + (bpm_event['y'] - last_y) * time_per_pulse
        new_timestamps.append(bpm_event['y'])
        last_event = bpm_event

    for y in note_y:
        time_per_pulse = ((60 / cur_bpm) * 4) / 960

        timestamp_at_y[y] = timestamp_at_y[cur_bpm_pulse] + (y - cur_bpm_pulse) * time_per_pulse
        new_timestamps.append(y)

        for bpm_event in bmson['bpm_events']:
            if y >= bpm_event['y']:
                cur_bpm = bpm_event['v']
                cur_bpm_pulse = bpm_event['y']

    return { k: round(timestamp_at_y[k] * 1000) for k in timestamp_at_y }


def bpm_at_offset(bmson, offset):
    cur_bpm = bmson['info']['init_bpm']

    for event in bmson['bpm_events']:
        if offset > event['y']:
            cur_bpm = event['v']

    return cur_bpm


def generate_konami_chart_from_bmson(bmson, keysounds_list, song_total_duration=None):
    # import json
    # print(json.dumps(bmson, indent=4))
    # exit(1)

    end_timestamp = 0
    end_measure = {
        'y': bmson['lines'][-1]['y'] + (bmson['lines'][-1]['y'] - bmson['lines'][-2]['y'])
    }

    bmson['lines'].append(end_measure)

    note_y = [x['y'] for x in list(itertools.chain(*[ks['notes'] for ks in bmson['sound_channels']]))]
    note_y = [x.get('l', 0) for x in list(itertools.chain(*[ks['notes'] for ks in bmson['sound_channels']]))]
    note_y += [x['y'] for x in bmson['lines']]
    note_y += [x['y'] for x in bmson['bpm_events']]

    # Timestamps for beats
    for idx, _ in enumerate(bmson['lines'][:-1]):
        cur_line = bmson['lines'][idx]
        next_line = bmson['lines'][idx+1]

        line_diff = next_line['y'] - cur_line['y']
        beats_per_measure = line_diff / bmson['info']['resolution']

        for i in range(int(beats_per_measure)):
            note_y.append(cur_line['y'] + (line_diff / beats_per_measure) * i)
            end_timestamp = cur_line['y'] + (line_diff / beats_per_measure) * (i + 1)

    real_note_y = sorted(list(set([float(x) for x in note_y])))

    for i in range(0, round(end_timestamp)):
        # TODO: Slow but working
        # This is required because the code to bump the timestamp when a keysound is played and loaded at the same time
        # uses non-existing timestamps
        note_y.append(i)

    note_y = sorted(list(set([float(x) for x in note_y])))

    # Pick up any left over y positions not found
    for sound in bmson['sound_channels']:
        for note in sound['notes']:
            if note['y'] not in note_y:
                note_y.append(note['y'])

    real_timestamps = calculate_timestamps(bmson, real_note_y)
    timestamps = calculate_timestamps(bmson, note_y)

    events = []

    # Measure line events
    last_measure_timestamp = 0
    for line_event in bmson['lines']:
        events.append({
            'name': "measure",
            'timestamp': timestamps[line_event['y']]
        })

        last_measure_timestamp = timestamps[line_event['y']]

    # Beat line events
    for idx, _ in enumerate(bmson['lines'][:-1]):
        cur_line = bmson['lines'][idx]
        next_line = bmson['lines'][idx+1]

        line_diff = next_line['y'] - cur_line['y']
        beats_per_measure = line_diff / bmson['info']['resolution']

        for i in range(int(beats_per_measure)):
            y = cur_line['y'] + (line_diff / beats_per_measure) * i

            events.append({
                'name': "beat",
                'timestamp': timestamps[y]
            })

    # BPM events
    events.append({
        'name': "bpm",
        'timestamp': 0,
        'bpm': round(bmson['info']['init_bpm'])
    })

    for bpm_event in bmson['bpm_events']:
        events.append({
            'name': "bpm",
            'timestamp': timestamps[bpm_event['y']],
            'bpm': round(bpm_event['v'])
        })

    # Time signature event
    # TODO: When exactly would this not be 4/4? pop'n 8 egypt has 3/4 or 4/3 (not sure which) but does it make any difference in-game?
    events.append({
        'name': "timesig",
        'timestamp': 0,
        'top': 4,
        'bottom': 4,
    })

    # End event
    events.append({
        'name': "end",
        'timestamp': timestamps[end_timestamp] if not song_total_duration else song_total_duration,
    })

    # Timing window stuff (How does this translate exactly? Frames?)
    timings = [
        0x76, # Early bad
        0x7a, # Early good
        0x7e, # Early great
        0x84, # Late great
        0x88, # Late good
        0x8c, # Late bad
    ]
    for idx, timing in enumerate(timings):
        events.append({
            'name': "timing",
            'timestamp': 0,
            'timing': timing,
            'timing_slot': idx
        })

    # Unknown event that all charts seem to have
    events.append({
        'name': "unk",
        'timestamp': 0,
        'value': 10,
    })

    # Key events
    button_mapping = {
        2.0: 0,
        4.0: 1,
        6.0: 2,
        8.0: 3,
        10.0: 4,
        14.0: 5,
        16.0: 6,
        18.0: 7,
        20.0: 8,
    }

    # The note events need to be in order or else the cur_button_loaded state won't be correct
    note_events = []
    for sound in bmson['sound_channels']:
        sound['name'] = sound['name'].lower()

        for note in sound['notes']:
            note_events.append((sound, note))

    note_events = sorted(note_events, key=lambda x:x[1]['y'])

    load_latest_window_offset = ((timings[1] - 128) * 16) - 16 # Early good
    load_latest_window_offset += -2 if load_latest_window_offset < 0 else 2

    load_window_bump_offset = ((timings[3] - 128) * 16) - 16 # Late great
    load_window_bump_offset += -2 if load_window_bump_offset < 0 else 2

    note_load_events = []
    cur_button_loaded = {}
    initial_keysounds = { k: 0 for k in range(0, 9) }
    for sound, note in note_events:
        if note['x'] not in button_mapping:
            if note['x'] != 0:
                print("Unknown button!", note)
                exit(1)

            else:
                events.append({
                    'name': "sample2",
                    'timestamp': timestamps[note['y']],
                    'value': keysounds_list.index(sound['name']) + 1,
                    'key': 8,  # TODO: What is this supposed to be exactly?
                })

        else:
            events.append({
                'name': "key",
                'timestamp': timestamps[note['y']],
                'key': button_mapping[note['x']],
                'length': timestamps[note['l']] - timestamps[note['y']] if note.get('l', 0) > 0 else 0,
                '_note': note,
                '_filename': sound['name']
            })

            if button_mapping[note['x']] not in cur_button_loaded or sound['name'] != cur_button_loaded[button_mapping[note['x']]]:
                # Find suitable timestamp to load keysound
                # There is a specific sweet spot window
                load_earliest_window = round(timestamps[note['y']] - (30000 / bpm_at_offset(bmson, note['y']))) # 1/2 of a beat of a measure at the current BPM
                load_latest_window = round(timestamps[note['y']] + load_latest_window_offset) # At the latest, load the keysound before the earliest part of an early good window

                candidate_timestamp = 0

                if load_earliest_window >= 0:
                    for k in timestamps:
                        if timestamps[k] >= load_earliest_window and k <= note['y']:
                            candidate_timestamp = k
                            break

                    for event in events:
                        if event.get('_note', None) == note:
                            continue

                        if event['timestamp'] >= timestamps[candidate_timestamp] and event['name'] == "key" and event['key'] == button_mapping[note['x']]:
                            # Bump timestamp when it would try to load a keysound in the same slot that's being played at the same timestamp
                            target = timestamps[candidate_timestamp] + load_window_bump_offset

                            while timestamps[candidate_timestamp] < target:
                                candidate_timestamp += 1

                if candidate_timestamp == 0:
                    initial_keysounds[note['key']] = keysounds_list.index(sound['name']) + 1

                else:
                    if timestamps[candidate_timestamp] >= load_latest_window:
                        diff = timestamps[candidate_timestamp] - load_latest_window
                        print("Potential issue with keysound load timing detected (%d ms off from sweet spot range):" % (diff))
                        print(timestamps[candidate_timestamp], load_latest_window)
                        print(sound['name'], note)

                        if diff < 50:
                            print("This has a high possibility of not loading this keysound in time for the button press")

                        else:
                            print("This may not cause issues in-game")

                        print()

                    events.append({
                        'name': "sample",
                        'timestamp': timestamps[candidate_timestamp],
                        'value': keysounds_list.index(sound['name']) + 1,
                        'key': button_mapping[note['x']],
                    })

                cur_button_loaded[button_mapping[note['x']]] = sound['name']

    # Initialize keysound samples
    for i in range(0, 9):
        events.append({
            'name': "sample",
            'timestamp': 0,
            'value': initial_keysounds[i],
            'key': i,
        })

    # Poor way of doing this, but I want the generated charts to be as close to official as possible including ordering of events
    events_by_timestamp = {}
    for event in sorted(events, key=lambda x:x['timestamp']):
        if event['timestamp'] not in events_by_timestamp:
            events_by_timestamp[event['timestamp']] = []

        events_by_timestamp[event['timestamp']].append(event)

    event_order = [
        "bpm",
        "timesig",
        "unk",
        "timing",
        "key",
        "sample",
        "sample2",
        "measure",
        "beat",
        "end",
    ]

    events_ordered = []
    for timestamp in events_by_timestamp:
        for event_name in event_order:
            events_by_name = []

            for event in events_by_timestamp[timestamp]:
                if event['name'] == event_name:
                    events_by_name.append(event)

            events_ordered += sorted(events_by_name, key=lambda x:x.get('key', 0))

    return events_ordered


def bmson_has_long_notes(bmson):
    for sound in bmson['sound_channels']:
        for note in sound['notes']:
            if note.get('l', 0) > 0:
                return True

    return False


def write_chart(events, output_filename, new_format):
    with open(output_filename, "wb") as outfile:
        bytecode_lookup = {
            "key": 0x0145,
            "sample": 0x0245,
            "unk": 0x0345,
            "bpm": 0x0445,
            "timesig": 0x0545,
            "end": 0x0645,
            "sample2": 0x0745,
            "timing": 0x0845,
            "measure": 0x0a00,
            "beat": 0x0b00,
        }

        for event in events:
            if event['timestamp'] < 0:
                continue

            outfile.write(int.to_bytes(event['timestamp'], 4, 'little'))
            outfile.write(int.to_bytes(bytecode_lookup[event['name']], 2, 'little'))

            if event['name'] == "bpm":
                outfile.write(int.to_bytes(event['bpm'], 2, 'little'))

            elif event['name'] == "timesig":
                outfile.write(int.to_bytes(event['bottom'], 1, 'little'))
                outfile.write(int.to_bytes(event['top'], 1, 'little'))

            elif event['name'] == "timing":
                outfile.write(int.to_bytes(event['timing'] | (event['timing_slot'] << 12), 2, 'little'))

            elif event['name'] == "unk":
                outfile.write(int.to_bytes(event['value'], 2, 'little'))

            elif event['name'] == "key":
                outfile.write(int.to_bytes(event['key'], 1, 'little'))
                outfile.write(int.to_bytes(0, 1, 'little')) # highlight zone

            elif event['name'] in ["sample", "sample2"]:
                outfile.write(int.to_bytes(event['value'] | (event['key'] << 12), 2, 'little'))

            elif event['name'] in ["measure", "beat", "end"]:
                outfile.write(int.to_bytes(0, 2, 'little'))

            else:
                print("Unknown name:", event['name'])
                exit(1)

            if new_format:
                if event['name'] in ['key'] and event['length'] > 0:
                    outfile.write(int.to_bytes(event['length'], 4, 'little'))

                else:
                    outfile.write(int.to_bytes(0, 4, 'little'))


def generate_wav(input_filename):
    new_filename = os.path.join("tmp", next(tempfile._get_candidate_names()) + ".wav")

    # Works for me in Windows and WSL with sox installed in Windows PATH
    # Remove .exe for Linux/Mac OS
    if os.path.exists("sox.exe") and on_wsl:
        os.system("""./sox.exe -G -S "%s" -e ms-adpcm "%s" """ % (input_filename, new_filename))

    else:
        os.system("""sox.exe -G -S "%s" -e ms-adpcm "%s" """ % (input_filename, new_filename))

    return new_filename


def generate_2dx(input_filenames, output_filename):
    # Based on mon's 2dxTools
    with open(output_filename, "wb") as outfile:
        # Write header
        header_title = os.path.splitext(os.path.basename(output_filename))[0][:16].encode('ascii')

        if len(header_title) < 16:
            header_title += b"\0" * (16 - len(header_title))

        file_offset = 0x48 + len(input_filenames) * 4
        outfile.write(header_title)
        outfile.write(int.to_bytes(file_offset, 4, 'little'))
        outfile.write(int.to_bytes(len(input_filenames), 4, 'little'))
        outfile.write(b"\0" * 0x30)

        for filename in input_filenames:
            outfile.write(int.to_bytes(file_offset, 4, 'little'))

            if not filename:
                continue

            file_offset += os.path.getsize(filename) + 24  # Size of file header

        for filename in input_filenames:
            if not filename:
                continue

            data = open(filename, "rb").read()

            outfile.write(b"2DX9")
            outfile.write(int.to_bytes(24, 4, 'little')) # Header size
            outfile.write(int.to_bytes(len(data), 4, 'little')) # Wave data size
            outfile.write(int.to_bytes(0x3231, 2, 'little')) # Always 0x3231
            outfile.write(int.to_bytes(0xffff, 2, 'little')) # trackId "always -1 for previews, 0-7 for song + effected versions, 9 to 11 used for a few effects"
            outfile.write(int.to_bytes(64, 2, 'little')) # "all 64, except song selection change 'click' is 40"
            outfile.write(int.to_bytes(1, 2, 'little')) # "0-127 for varying quietness"
            outfile.write(int.to_bytes(0, 4, 'little')) # "sample to loop at * 4"
            outfile.write(data)


def export_2dx(keysounds, output_filename):
    os.makedirs("tmp", exist_ok=True)

    temp_filenames = [None] * len(keysounds)

    try:
        for idx, input_filename in enumerate(keysounds):
            if not input_filename or not os.path.exists(input_filename):
                if input_filename:
                    print("Couldn't find", input_filename)
                    exit(1)
                continue

            new_filename = generate_wav(input_filename)

            if os.path.exists(new_filename):
                temp_filenames[idx] = new_filename

            else:
                print("Couldn't find", input_filename)
                exit(1)

        generate_2dx(temp_filenames, output_filename)

    finally:
        for filename in temp_filenames:
            if filename and os.path.exists(filename):
                os.remove(filename)


def generate_render(input_filename, output_filename):
    if not os.path.exists("bmx2wavc.exe"):
        print("bmx2wavc.exe is required to generate previews")
        exit(1)

    if on_wsl:
        os.system("""./bmx2wavc.exe "%s" "%s" """ % (input_filename, output_filename))

    else:
        os.system("""bmx2wavc.exe "%s" "%s" """ % (input_filename, output_filename))


def get_duration(input_filename):
    if not os.path.exists(input_filename):
        return None

    sound_file = pydub.AudioSegment.from_file(input_filename)

    return len(sound_file)


def generate_preview(input_filename, output_filename, offset, duration):
    sound_file = pydub.AudioSegment.from_file(input_filename)

    if offset < 0:
        # Set offset of preview to middle of song
        offset = len(sound_file) / 2 / 1000

    sound_file = sound_file[offset * 1000 : (offset + duration) * 1000]
    sound_file = sound_file.fade_out(500)
    sound_file.export(output_filename, format="wav")

    return output_filename


def get_real_keysound_filename(input_filename, keysounds_folder):
    
    if not input_filename:
        return None

    target_path = os.path.join(keysounds_folder, input_filename)

    if os.path.exists(target_path):
        # The file exists already
        return target_path
    
    extensions = [".wav",".ogg"]
    # The file doesn't exist, so try to match it with other extensions
    for extension in extensions:
     target_path = os.path.join(keysounds_folder, ("%s"+ extension) % (os.path.splitext(input_filename)[0]))
     if os.path.exists(target_path):
         # The file exists already
         return target_path


    print("Couldn't find", input_filename)
    exit(1)

    return None


def create_banner(output_path, musicid, banner_filename):
    banner_image = Image.open(banner_filename)

    if banner_image.size != (244, 58):
        print("Banner must be 244x58! Found", banner_image.size)
        exit(1)

    banner_name = "kc_%04d" % (musicid)
    banner_output_folder = os.path.join(output_path, banner_name)
    os.makedirs(os.path.join(banner_output_folder, "tex"), exist_ok=True)

    open(os.path.join(banner_output_folder, "magic"), "wb").write(b"NGPF")
    open(os.path.join(banner_output_folder, "cversion"), "wb").write(b"1.3.72\0")

    banner_xml = E.texturelist(
        E.texture(
            E.size(
                "256 64",
                __type="2u16",
            ),
            E.image(
                E.uvrect(
                    "2 490 2 118",
                    __type="4u16"
                ),
                E.imgrect(
                    "0 492 0 120",
                    __type="4u16"
                ),
                name=banner_name
            ),
            format="argb8888rev",
            mag_filter="nearest",
            min_filter="nearest",
            name="tex000",
            wrap_s="clamp",
            wrap_t="clamp",
        ),
        compress="avslz",
    )

    tex_path = os.path.join(banner_output_folder, "tex")
    open(os.path.join(tex_path, "texturelist.xml"), "wb").write(tostring(banner_xml, pretty_print=True, method='xml', encoding='utf-8', xml_declaration=True))

    if banner_image.size == (244, 58):
        # Duplicate the edge pixels
        new_banner_image = Image.new('RGBA', (banner_image.width + 2, banner_image.height + 2))
        new_banner_image.paste(banner_image, (1, 1))
        new_banner_image.paste(banner_image.crop((0, 0, banner_image.width, 1)), (1, 0)) # Top
        new_banner_image.paste(banner_image.crop((0, banner_image.height - 1, banner_image.width, banner_image.height)), (1, banner_image.height + 1)) # Bottom
        # new_banner_image.paste(banner_image.crop((1, 0, 2, banner_image.height)), (0, 1)) # Left
        new_banner_image.paste(banner_image.crop((banner_image.width - 1, 0, banner_image.width, banner_image.height)), (banner_image.width + 1, 1)) # Right
        banner_image = new_banner_image

    if banner_image.size not in [(246, 60)]:
        print("Unknown banner size", banner_filename, banner_image.size)
        exit(1)

    banner_image.save(os.path.join(tex_path, banner_name + ".png"))

    return banner_name


def create_bg(output_path, musicid, bg_filename):
    bg_image = Image.open(bg_filename)

    if bg_image.size != (128, 256):
        print("Background must be 128x256! Found", bg_image.size)
        exit(1)

    bg_name = "bg_%04d" % (musicid)
    bg_output_folder = os.path.join(output_path, bg_name)
    os.makedirs(os.path.join(bg_output_folder, "tex"), exist_ok=True)

    open(os.path.join(bg_output_folder, "magic"), "wb").write(b"NGPF")
    open(os.path.join(bg_output_folder, "cversion"), "wb").write(b"1.3.72\0")

    bg_xml = E.texturelist(
        E.texture(
            E.size(
                "256 512",
                __type="2u16",
            ),
            E.image(
                E.uvrect(
                    "2 258 2 514",
                    __type="4u16"
                ),
                E.imgrect(
                    "0 260 0 516",
                    __type="4u16"
                ),
                name=bg_name
            ),
            format="argb8888rev",
            mag_filter="nearest",
            min_filter="nearest",
            name="tex000",
            wrap_s="clamp",
            wrap_t="clamp",
        ),
        compress="avslz",
    )

    tex_path = os.path.join(bg_output_folder, "tex")
    open(os.path.join(tex_path, "texturelist.xml"), "wb").write(tostring(bg_xml, pretty_print=True, method='xml', encoding='utf-8', xml_declaration=True))

    if bg_image.size == (128, 256):
        # Duplicate the edge pixels
        new_bg_image = Image.new('RGBA', (bg_image.width + 2, bg_image.height + 2))
        new_bg_image.paste(bg_image, (1, 1))
        new_bg_image.paste(bg_image.crop((0, 0, bg_image.width, 1)), (1, 0)) # Top
        new_bg_image.paste(bg_image.crop((0, bg_image.height - 1, bg_image.width, bg_image.height)), (1, bg_image.height + 1)) # Bottom
        # new_bg_image.paste(bg_image.crop((1, 0, 2, bg_image.height)), (0, 1)) # Left
        new_bg_image.paste(bg_image.crop((bg_image.width - 1, 0, bg_image.width, bg_image.height)), (bg_image.width + 1, 1)) # Right
        bg_image = new_bg_image

    if bg_image.size not in [(130, 258)]:
        print("Unknown background size", bg_filename, bg_image.size)
        exit(1)

    bg_image.save(os.path.join(tex_path, bg_name + ".png"))

    return bg_name


def create_hariai(output_path, musicid, hariai_filename):
    hariai_image = Image.open(hariai_filename)

    if (hariai_image.size != (250, 322)) and (hariai_image.size != (382, 502)):
        print("hariai must be (250, 322) or (382, 502)! Found", hariai_image.size)
        exit(1)

    hariai_name = "ha_%04d" % (musicid)
    hariai_output_folder = os.path.join(output_path, hariai_name)
    os.makedirs(os.path.join(hariai_output_folder, "tex"), exist_ok=True)

    open(os.path.join(hariai_output_folder, "magic"), "wb").write(b"NGPF")
    open(os.path.join(hariai_output_folder, "cversion"), "wb").write(b"1.3.72\0")
    #texture xml parameters depending on the size 
    xml_texture_data = [["256 512", "2 498 2 642", "0 500 0 644"], ["512 512", "2 762 2 1002", "0 764 0 1004"]] 
    image_type = 0
    #in case our image is the second type will use that
    if hariai_image.size == (382, 502):
        image_type = 1
         
    hariai_xml = E.texturelist(
        E.texture(
            E.size(
                xml_texture_data[image_type][0],
                __type="2u16",
            ),
            E.image(
                E.uvrect(
                    xml_texture_data[image_type][1],
                    __type="4u16"
                ),
                E.imgrect(
                    xml_texture_data[image_type][2],
                    __type="4u16"
                ),
                name=hariai_name
            ),
            format="argb8888rev",
            mag_filter="nearest",
            min_filter="nearest",
            name="tex000",
            wrap_s="clamp",
            wrap_t="clamp",
        ),
        compress="avslz",
    )

    tex_path = os.path.join(hariai_output_folder, "tex")
    open(os.path.join(tex_path, "texturelist.xml"), "wb").write(tostring(hariai_xml, pretty_print=True, method='xml', encoding='utf-8', xml_declaration=True))


    hariai_image.save(os.path.join(tex_path, hariai_name + ".png"))

    return hariai_name


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    difficulties = ['bp', 'ep', 'np', 'hp', 'op']

    for difficulty in difficulties:
        parser.add_argument('--input-%s' % difficulty, help='Input file (%s)' % difficulty.upper(), default=None)

    #Display required arguments on help
    requiredNamed = parser.add_argument_group('required arguments')
    #Arguments
    parser.add_argument('--output', help='Output folder', default="output")
    requiredNamed.add_argument('--name', help='Base name used for output', default=None, required=True)
    requiredNamed.add_argument('--musicid', help='Music ID used for the database file', required=True, type=int)
    requiredNamed.add_argument('--keysounds-folder', help='Input folder containing keysounds', default=None, required=True)
    parser.add_argument('--preview', help='Input preview file (overrides preview generation code)', default=None)
    parser.add_argument('--new', help='New chart format which supports hold notes', default=False, action='store_true')
    requiredNamed.add_argument('--banner', help='Banner image (must be 244x58)', default=None, required=True)
    parser.add_argument('--bg', help='Background image (must be 128x256)', default=None, required=False)
    parser.add_argument('--hariai', help='Hariai image (must be 250x322 or 382x502)', default=None)
    parser.add_argument('--metadata-fw-title', help='Fullwidth music title for database', default=None)
    parser.add_argument('--metadata-fw-artist', help='Fullwidth music artist for database', default=None)
    parser.add_argument('--metadata-fw-genre', help='Fullwidth music genre for database', default=None)
    parser.add_argument('--metadata-title', help='Music title for database', default=None)
    parser.add_argument('--metadata-artist', help='Music artist for database', default=None)
    parser.add_argument('--metadata-genre', help='Music genre for database', default=None)
    parser.add_argument('--metadata-chara1', help='Chara1 for database', default=None)
    parser.add_argument('--metadata-chara2', help='Chara2 for database', default=None)
    parser.add_argument('--metadata-has-battle-hyper', help='Battle Hyper flag for database', default=False, action='store_true')
    parser.add_argument('--metadata-hariai-is-jacket', help='Jacket mask flag for database', default=False, action='store_true')
    parser.add_argument('--metadata-folder', help='Folder entry for database', default=0, type=int)
    parser.add_argument('--metadata-categories', help='Categories entry for database', default=0, type=int)
    parser.add_argument('--metadata-cs-version', help='CS version entry for database', default=0, type=int)
    parser.add_argument('--metadata-mask', help='Base mask value for database', default=0, type=int)
    parser.add_argument('--metadata-chara-x', help='Chara X entry for database', default=0, type=int)
    parser.add_argument('--metadata-chara-y', help='Chara Y entry for database', default=0, type=int)
    
    
    if os.path.exists("bmx2wavc.exe"):
        parser.add_argument('--preview-offset', help='Offset from start in seconds (ex. 10.4 would be 10.4 seconds)', default=-1, type=float)
        parser.add_argument('--preview-duration', help='Length of preview in seconds', default=10, type=float)

    args = parser.parse_args()
    args_vars = vars(args)

    if args.bg is None:
        print("warning: no background specified, will only work with usaneko and up")
    if args.musicid < 4000:
        print("Music ID must be >= 4000")
        exit(1)

    output_path = os.path.join(args.output, args.name)

    mask = args.metadata_mask
    charts_xml = []

    # Generate list of keysounds based on input charts
    bms_charts = []
    chart_filenames = []
    battle_chart = None
    for difficulty in difficulties:
        if not args_vars.get('input_%s' % difficulty, None):
            continue

        output_filename = os.path.join(output_path, "%s_%s.bin" % (args.name, difficulty))

        bms = bms2bmson()
        bms.Convert(args_vars['input_%s' % difficulty])
        bms_charts.append((bms, output_filename))

        has_hold_notes = bmson_has_long_notes(bms.bmson)

        optional = []
        if has_hold_notes or args.new:
            optional.append(
                E.force_new_chart_format("1", __type="u32")
            )

            args.new = True  # In case the song has long notes and the user forgot to set the new flag, upgrade it automatically

        chart = E.chart(
            E.folder("custom", __type="str"),
            E.filename(args.name, __type="str"),
            E.audio_param1("0", __type="s32"),
            E.audio_param2("0", __type="s32"),
            E.audio_param3("0", __type="s32"),
            E.audio_param4("0", __type="s32"),
            E.file_type("0", __type="u32"),
            E.used_keys("0", __type="u16"),
            E.diff("1", __type="u8"),
            E.hold_flag("1" if has_hold_notes else "0", __type="u8"),
            idx=str(difficulty),
            *optional
        )
        charts_xml.append(chart)

        if difficulty == "bp":
            battle_chart = chart

        chart_filenames.append(args_vars['input_%s' % difficulty])

    if args.metadata_has_battle_hyper and battle_chart is not None:
        chart = copy.deepcopy(battle_chart)
        chart.set('idx', 'bp_h')
        charts_xml.append(chart)

    # Generate list of keysounds used in the input charts to create the keysound .2dx
    keysounds_list = []
    for bms, _ in bms_charts:
        for keysound in sorted(bms.wavHeader, key=lambda x:x['ID']):
            if keysound['name'] not in keysounds_list:
                keysounds_list.append(keysound['name'].lower())

    # Render chart so it can be used to find the true length of the song and also later for preview generation if required
    render_filename = os.path.join("tmp", "%s_full.wav" % args.name)
    generate_render(chart_filenames[-1], render_filename)
    song_total_duration = get_duration(render_filename)

    os.makedirs(output_path, exist_ok=True)
    for bms, output_filename in bms_charts:
        write_chart(generate_konami_chart_from_bmson(bms.bmson, keysounds_list, song_total_duration), output_filename, new_format=args.new)

    real_keysound_filenames = [(x, get_real_keysound_filename(x, args.keysounds_folder)) for x in keysounds_list]
    export_2dx([x[1] for x in real_keysound_filenames], os.path.join(output_path, "%s.2dx" % args.name))

    if args.preview:
        # Create a _pre.2dx if a preview is specified
        export_2dx([args.preview], os.path.join(output_path, "%s_pre.2dx" % args.name))

    else:
        preview_filename = os.path.join("tmp", "%s_pre.wav" % args.name)

        if not render_filename or not os.path.exists(render_filename):
            render_filename = os.path.join("tmp", "%s_full.wav" % args.name)
            generate_render(chart_filenames[-1], render_filename)

        generate_preview(render_filename, preview_filename, args.preview_offset, args.preview_duration)
        export_2dx([preview_filename], os.path.join(output_path, "%s_pre.2dx" % args.name))

        os.unlink(preview_filename)

    if os.path.exists(render_filename):
        os.unlink(render_filename)

    tex_files = {}
    if args.banner:
        # Create banner folder
        tex_files['kc_diff_ifs'] = create_banner(output_path, args.musicid, args.banner)

    if args.hariai:
        # Create hariai folder
        tex_files['ha_merge_ifs'] = create_hariai(output_path, args.musicid, args.hariai)
        mask |= 0x00800000  # Required for songs that show a hariai image on the music selection screen

    if args.bg:
        # Create background folder
        tex_files['bg_diff_ifs'] = create_bg(output_path, args.musicid, args.bg)

    if args.metadata_hariai_is_jacket:
        mask |= 0x00000020  # The alternate hariai image (set by using 0x800000) is a song jacket instead of a character portrait

    xml = E.music(
        E.fw_genre(args.metadata_fw_genre if args.metadata_fw_genre else "", __type="str"),
        E.fw_title(args.metadata_fw_title if args.metadata_fw_title else "", __type="str"),
        E.fw_artist(args.metadata_fw_artist if args.metadata_fw_artist else "", __type="str"),
        E.genre(args.metadata_genre if args.metadata_genre else "", __type="str"),
        E.title(args.metadata_title if args.metadata_title else "", __type="str"),
        E.artist(args.metadata_artist if args.metadata_artist else "", __type="str"),
        E.chara1(args.metadata_chara1 if args.metadata_chara1 else "", __type="str"),
        E.chara2(args.metadata_chara2 if args.metadata_chara2 else "", __type="str"),
        E.mask(str(mask), __type="u32"),
        E.folder(str(args.metadata_folder), __type="u32"),
        E.cs_version(str(args.metadata_cs_version), __type="u32"),
        E.categories(str(args.metadata_categories), __type="u32"),
        E.charts(*charts_xml),
        E.ha(tex_files.get('ha_merge_ifs', ""), __type="str"),
        E.chara_x(str(args.metadata_chara_x), __type="u32"),
        E.chara_y(str(args.metadata_chara_y), __type="u32"),
        E.unk1("0 0 0 0 0 0 36 0 0 59 77 0 0 0 0 134 0 0 68 67 222 0 0 0 0 0 0 0 0 0 0 0", __type="u16", __count="32"),
        E.display_bpm(" ".join([str(x) for x in [0] * 12]), __type="u16", __count="12"),
        id=str(args.musicid)
    )

    db_path = os.path.join(args.output, "db")
    os.makedirs(db_path, exist_ok=True)

    output_xml_path = os.path.join(db_path, "custom_musicdb.xml")

    # Try to read in existing database and merge if possible
    if os.path.exists(output_xml_path):
        print("Merging databases")
        xml_full = etree_parse(output_xml_path, XMLParser(remove_blank_text=True)).getroot()

        remove = []
        musicid_str = "%04d" % args.musicid
        for entry in xml_full.findall('music'):
            if entry.get('id') == musicid_str:
                remove.append(entry)

        for entry in remove:
            xml_full.remove(entry)

        xml_full.append(xml)
        xml = xml_full

    else:
        xml = E.database(
            xml
        )

    open(output_xml_path, "wb").write(tostring(xml, method='xml', encoding='cp932', xml_declaration=True))
    xml = etree_parse(output_xml_path, XMLParser(remove_blank_text=True)).getroot()
    open(output_xml_path, "wb").write(tostring(xml, pretty_print=True, method='xml', encoding='cp932', xml_declaration=True).replace(b"cp932", b"shift-jis"))

    # Create .ifs instead of folder
    target_output_path = output_path

    for path in tex_files:
        folder = tex_files[path]
        target_output_path = os.path.join(args.output, "data", "tex", "system", path)
        target_path = os.path.join(output_path, folder)

        os.makedirs(target_output_path, exist_ok=True)

        subprocess.call('"%s" -c "from ifstools import ifstools; ifstools.main()" -s --no-cache -y "%s" -o "%s"' % (sys.executable, target_path, target_output_path), shell=True)
        shutil.rmtree(target_path)

    target_output_path = os.path.join(args.output, "data", "sd", "custom")
    os.makedirs(target_output_path, exist_ok=True)
    subprocess.call('"%s" -c "from ifstools import ifstools; ifstools.main()" -s --no-cache -y "%s" -o "%s"' % (sys.executable, output_path, target_output_path), shell=True)
    shutil.rmtree(output_path)

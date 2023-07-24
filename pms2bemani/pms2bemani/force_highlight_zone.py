import os
import sys

input_filename = sys.argv[1]
start_note = int(sys.argv[2])
end_note = int(sys.argv[3])
highlight_flag = int(sys.argv[4])

data = bytearray(open(input_filename, "rb").read())
header = data[:0x100]

type1_count = list(set([header[i] for i in range(4, len(header), 8) if header[i] != 0]))
type2_count = list(set([header[i] for i in range(4, len(header), 12) if header[i] != 0]))

is_type2 = len(type1_count) != 1

event_size = 12 if is_type2 else 8

events = []
note_count = 0
for i in range(0, len(data), event_size):
    event_data = data[i:i+event_size]

    if event_data[5] == 1:
        note_count += 1

        if note_count >= start_note and note_count <= end_note:
            event_data[7] = highlight_flag

    events.append(event_data)

open(input_filename, "wb").write(b"".join(events))
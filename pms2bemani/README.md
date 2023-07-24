## Requirements

1) To install the requirements needed (ifstools, pydub): `python3 -m pip install -r requirements.txt`
2) Install sox (https://sourceforge.net/projects/sox/files/sox/14.4.2/) and include it in your system PATH or put sox.exe in the folder with `pms2bemani.py`

## Usage
```
usage: pms2bemani.py [-h] [--input-bp INPUT_BP] [--input-ep INPUT_EP]
                     [--input-np INPUT_NP] [--input-hp INPUT_HP]
                     [--input-op INPUT_OP] --name NAME --keysounds-folder
                     KEYSOUNDS_FOLDER [--preview PREVIEW] [--new] [--ifs]
                     [--preview-offset PREVIEW_OFFSET]
                     [--preview-duration PREVIEW_DURATION]

optional arguments:
  -h, --help            show this help message and exit
  --input-bp INPUT_BP   Input file (BP)
  --input-ep INPUT_EP   Input file (EP)
  --input-np INPUT_NP   Input file (NP)
  --input-hp INPUT_HP   Input file (HP)
  --input-op INPUT_OP   Input file (OP)
  --name NAME           Base name used for output
  --keysounds-folder KEYSOUNDS_FOLDER
                        Input folder containing keysounds
  --preview PREVIEW     Input preview file (optional, overrides preview
                        generation code)
  --new                 New chart format which supports hold notes
  --ifs                 Create IFS output instead of folder output (requires
                        ifstools)
  --preview-offset PREVIEW_OFFSET
                        Offset from start in seconds (ex. 10.4 would be 10.4
                        seconds)
  --preview-duration PREVIEW_DURATION
                        Length of preview in seconds
```

- Use `--new` to specify the new chart format (Usaneko and later) which supports hold notes.
- Use `--ifs` to generate an `.ifs` file instead of a folder.
- If a preview sound file is not specified with --preview, a preview will be automatically generated.
    - Automatically generated previews default to 10 seconds at the mid point of the chart.
    - The preview offset and duration can be customized using `--preview-offset` and `--preview-duration` respectively.

Example: `python3 pms2bemani.py --input-np wonderingbeats/01_kouunn-n.pms --input-hp wonderingbeats/02_kouunn-h.pms --input-op wonderingbeats/03_kouunn-ex.pms --keysounds-folder wonderingbeats --name wonderingbeats_convert --ifs --new --preview-offset 10.4 --preview-duration 15`

## Credits
- ifstools (https://github.com/mon/ifstools)
- 2dxTools (https://github.com/mon/2dxTools)
- bmx2wav (http://childs.squares.net/program/bmx2wav/)
- bms2bmson-python (https://github.com/iidx/bms2bmson-python)

## Requirements

1) To install the requirements needed (ifstools, pydub): `python3 -m pip install -r requirements.txt`
2) Install sox (https://sourceforge.net/projects/sox/files/sox/14.4.2/) and include it in your system PATH or put sox.exe in the folder with `pms2bemani.py`

## Usage
```
usage: pms2bemani.py [-h] [--input-bp INPUT_BP] [--input-ep INPUT_EP] [--input-np INPUT_NP] [--input-hp INPUT_HP] [--input-op INPUT_OP] [--output OUTPUT] --name NAME
                     --musicid MUSICID --keysounds-folder KEYSOUNDS_FOLDER [--preview PREVIEW] [--new] --banner BANNER [--bg BG] [--hariai HARIAI]
                     [--metadata-fw-title METADATA_FW_TITLE] [--metadata-fw-artist METADATA_FW_ARTIST] [--metadata-fw-genre METADATA_FW_GENRE]
                     [--metadata-title METADATA_TITLE] [--metadata-artist METADATA_ARTIST] [--metadata-genre METADATA_GENRE] [--metadata-chara1 METADATA_CHARA1]
                     [--metadata-chara2 METADATA_CHARA2] [--metadata-has-battle-hyper] [--metadata-hariai-is-jacket] [--metadata-folder METADATA_FOLDER]
                     [--metadata-categories METADATA_CATEGORIES] [--metadata-cs-version METADATA_CS_VERSION] [--metadata-mask METADATA_MASK]
                     [--metadata-chara-x METADATA_CHARA_X] [--metadata-chara-y METADATA_CHARA_Y] [--preview-offset PREVIEW_OFFSET] [--preview-duration PREVIEW_DURATION]

optional arguments:
  -h, --help            show this help message and exit
  --input-bp INPUT_BP   Input file (BP)
  --input-ep INPUT_EP   Input file (EP)
  --input-np INPUT_NP   Input file (NP)
  --input-hp INPUT_HP   Input file (HP)
  --input-op INPUT_OP   Input file (OP)
  --output OUTPUT       Output folder
  --preview PREVIEW     Input preview file (overrides preview generation code)
  --new                 New chart format which supports hold notes
  --bg BG               Background image (must be 128x256)
  --hariai HARIAI       Hariai image (must be 250x322 or 382x502)
  --metadata-fw-title METADATA_FW_TITLE
                        Fullwidth music title for database
  --metadata-fw-artist METADATA_FW_ARTIST
                        Fullwidth music artist for database
  --metadata-fw-genre METADATA_FW_GENRE
                        Fullwidth music genre for database
  --metadata-title METADATA_TITLE
                        Music title for database
  --metadata-artist METADATA_ARTIST
                        Music artist for database
  --metadata-genre METADATA_GENRE
                        Music genre for database
  --metadata-chara1 METADATA_CHARA1
                        Chara1 for database
  --metadata-chara2 METADATA_CHARA2
                        Chara2 for database
  --metadata-has-battle-hyper
                        Battle Hyper flag for database
  --metadata-hariai-is-jacket
                        Jacket mask flag for database
  --metadata-folder METADATA_FOLDER
                        Folder entry for database
  --metadata-categories METADATA_CATEGORIES
                        Categories entry for database
  --metadata-cs-version METADATA_CS_VERSION
                        CS version entry for database
  --metadata-mask METADATA_MASK
                        Base mask value for database
  --metadata-chara-x METADATA_CHARA_X
                        Chara X entry for database
  --metadata-chara-y METADATA_CHARA_Y
                        Chara Y entry for database
  --preview-offset PREVIEW_OFFSET
                        Offset from start in seconds (ex. 10.4 would be 10.4 seconds)
  --preview-duration PREVIEW_DURATION
                        Length of preview in seconds

required arguments:
  --name NAME           Base name used for output
  --musicid MUSICID     Music ID used for the database file
  --keysounds-folder KEYSOUNDS_FOLDER
                        Input folder containing keysounds
  --banner BANNER       Banner image (must be 244x58)
```

- Use `--new` to specify the new chart format (Usaneko and later) which supports hold notes.
- If a preview sound file is not specified with --preview, a preview will be automatically generated.
    - Automatically generated previews default to 10 seconds at the mid point of the chart.
    - The preview offset and duration can be customized using `--preview-offset` and `--preview-duration` respectively.

Example: `python3 pms2bemani.py --input-np wonderingbeats/01_kouunn-n.pms --input-hp wonderingbeats/02_kouunn-h.pms --input-op wonderingbeats/03_kouunn-ex.pms --keysounds-folder wonderingbeats --name wonderingbeats_convert --new --preview-offset 10.4 --preview-duration 15`

## GUI for pms2bemani

GUI and manager for pms2bemani.
This script needs to be in the same folder as pms2bemani.py and gui_assets.


## Credits
- ifstools (https://github.com/mon/ifstools)
- 2dxTools (https://github.com/mon/2dxTools)
- bmx2wav (http://childs.squares.net/program/bmx2wav/)
- bms2bmson-python (https://github.com/iidx/bms2bmson-python)

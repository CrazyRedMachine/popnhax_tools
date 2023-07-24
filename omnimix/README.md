# Omnimix documentation

Refer to [omnimix_db.md](omnimix_db.md)

# Omnimix tools

## ida_find_addrs.py

IDA script tested in 6.6 and 7.x.
Creates a map file based on the opened DLL file.
The output file is not guaranteed to work but it should be about 95% right.
If the game crashes when you use a newly generated XML file, diff with a known good/working XML file to figure out what patches don't look right and remove them.

Usage:
1. Load popn22.dll in IDA Pro
2. Wait until IDA finishes analyzing the entire DLL
3. File > Script file... > select ida_find_addrs.py
4. Copy output XML file from IDA's output window (by default it will be docked to the bottom of the screen)


## db_dump.py

Dump the full database information from the specified DLL using the input XML mapping information.
You can obtain the XML maps by using ida_find_addrs.py.

Usage:
```bash
> python3 db_dump.py --help
usage: db_dump.py [-h] --input-dll INPUT_DLL --input-xml INPUT_XML
                  [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --input-dll INPUT_DLL
                        Input DLL file
  --input-xml INPUT_XML
                        Input XML file
  --output OUTPUT       Output folder
```

Example: `python3 db_dump.py --input-dll popn22.dll --input-xml db/patches_2018082100.xml --output 2018082100`


## verify_data.py

Verify the integrity of the game's data. This checks to make sure that all of the expected chart files, previews, and certain images are as expected.
Chart data itself is verified using various criteria for what I felt a "standard" chart would be.
Not all charts, including official charts, meet this criteria but still work in-game.

WARNING: This tool is slow because it checks all song-related IFS files, including verifying all of the charts as much as possible.

Usage:
```bash
> python3 verify_data.py --help
usage: verify_data.py [-h] --input-dll INPUT_DLL --input-xml INPUT_XML
                      --input-data INPUT_DATA [--input-db INPUT_DB]

optional arguments:
  -h, --help            show this help message and exit
  --input-dll INPUT_DLL
                        Input DLL file
  --input-xml INPUT_XML
                        Input XML file
  --input-data INPUT_DATA
                        Input data folder
  --input-db INPUT_DB   Input db folder
```

Example: `python3 verify_data.py --input-dll popn22.dll --input-xml db/patches_2018082100.xml --input-data data --input-db db`

# Other Important Notes

- ~~As of time of writing, the latest version of ifstools (1.14) will not extract jacket.ifs properly on Windows due to NTFS's case-insensitivity, resulting in 3 images being overwritten with data that won't work in-game. You can extract on a *nix system to get the correct jacket images if you see a green block in place of the jackets for the affected songs.~~
  - Not pushed out to pypi yet, but this has already been fixed in master and will be included in the next release of ifstools where you can use the `--rename-dupes` flag (thanks mon!).

- Character database editing is slightly restrictive at the moment due to not being able to add new entries to the flavor table. When trying to add new entries to the flavor table there is a high chance of the game crashing in my experience. My guess is that there are some more places that should be patched that I have not found yet. This is a technical issue that could be solved with more work but it's more of a stretch goal than a main goal for this project so I put in a bandaid to make sure that the flavor table never expands. This issue is also why some unlocked characters will turn into Nyami alts.
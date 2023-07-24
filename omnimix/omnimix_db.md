# Good practice for custom chart makers

## Database structure

Use this url to avoid songid collisions with other chart makers
[community spreadsheet](https://docs.google.com/spreadsheets/d/18qPEH5OZH67Blq6ySlHRnxxfmojFmgG7GQ80Wyd21zY/edit?usp=sharing)

- do not use hiragana or kanji in the `fw_genre`/`fw_title`/`fw_artist` fields, they are used to sort the songlist. Only use full-width S-JIS characters.
- use only lowercase filenames both inside your .ifs and for the .ifs themselves
- it is not required to use lowercase filenames for the .xml files but it's better to do it
- use a unique sd subfolder name (e.g. sd/custom_milo/) to avoid filename collision with other packs 

## Folder structure 

- the song pack should go in `data_mods`
- you should have a unique folder name for your mod (e.g. `data_mods\crm_custom_2`)
- database files must go in your mod folder root (e.g. `data_mods\crm_custom_2\custom_musicdb_crm2.xml`)
- all sound data .ifs must go in the sd subfolder and within another unique folder name to avoid collision with other packs (e.g. `data_mods\crm_custom_2\sd\crm_custom\despacito.ifs`)
- ha_merge.ifs, kc_diff.ifs and other files should follow the original data structure (e.g. `data_mods\crm_custom_2\tex\system\ha_merge_ifs\ha_despacito.ifs`.
- Thanks to mon's LayeredFS, any file from the `data` folder can be modded this way
- NOTE: do not pack an .ifs file unless it is meant to hide some files from the game. For example it is ok to have several mods with a `ha_merge_ifs` folder, but do not use a `ha_merge.ifs` file or it will entirely replace the original file rather than merging with it.

- **IMPORTANT NOTE**: use only lowercase filenames both inside your .ifs and for the .ifs themselves. Failing to do so might crash the game.
- Make sure your xml files are shift-jis encoded, else your songs won't appear ingame.

# Omnimix databases documentation

## database load order

All database files that are to be loaded must reside in data_mods/your_mod_name/
They will be loaded in alphabetical order so name them with respect to the order you want them to be loaded. Also be mindful of your own mod folder name.

Example:
```
/data_mods
  /crm_custom_1
      /custom_musicdb_crm1.xml
      /custom_musicdb_zzz.xml
  /milo_custom_2
      /custom_musicdb_milo2.xml
```
custom_musicdb_crm1.xml and custom_musicdb_zzz.xml will be loaded first (in this order), because of the folder name.

NOTE: popnhax will load all character data from all mod folders before loading any music data, regardless of the order.

The same `id` can be listed in multiple files. For example, music ID 100 can be in both `omnimix_musicdb_0.xml` and `omnimix_musicdb_1.xml`. In that case, the data specified in the file loaded later will overwrite the previously loaded data.

Both the music database and character database XML files allow for partial loading. That is, you can specify only the data you wish to modify instead of copying all of the information associated with that entry. This is useful, for example, if you want to change a song's title, difficulty, add a single chart, etc.

For example, this is a valid database file that will patch only the specified data:
```xml
<?xml version='1.0' encoding='shift-jis'?>
<database>
  <music idx="1">
    <title __type="str">New Title</title>
  </music>
  <music idx="2">
    <genre __type="str">New Genre</genre>
  </music>
  <music idx="3">
    <charts>
        <chart idx="hp">
            <diff __type="u8">12</diff>
        </chart>
    </charts>
  </music>
  <chara idx="100">
    <disp_name __type="str">New Chara Name</disp_name>
  </music>
</database>
```

## Music database format

```xml
<music id="3000">
    <fw_genre __type="str">ニューカマー</fw_genre>
    <fw_title __type="str">ＵＮ－ＢＡＬＡＮＣＥ</fw_title>
    <fw_artist __type="str">サトウチアキ</fw_artist>
    <genre __type="str">ニューカマー</genre>
    <title __type="str">un-Balance</title>
    <artist __type="str">佐藤千晶</artist>
    <chara1 __type="str">kate_3a</chara1>
    <chara2 __type="str">kate_3b</chara2>
    <mask __type="u32">32</mask>
    <folder __type="u32">3</folder>
    <cs_version __type="u32">0</cs_version>
    <categories __type="u32">0</categories>
    <charts>
        <chart idx="np">
            <folder __type="str">omni_cs</folder>
            <filename __type="str">ac3_newcommer_0</filename>
            <audio_param1 __type="s32">50</audio_param1>
            <audio_param2 __type="s32">50</audio_param2>
            <audio_param3 __type="s32">0</audio_param3>
            <audio_param4 __type="s32">0</audio_param4>
            <file_type __type="u32">0</file_type>
            <used_keys __type="u16">0</used_keys>
            <diff __type="u8">24</diff>
            <hold_flag __type="u8">0</hold_flag>
        </chart>
    </charts>
    <ha __type="str"></ha>
    <chara_x __type="u32">0</chara_x>
    <chara_y __type="u32">0</chara_y>
    <unk1 __type="u16" __count="32">0 0 0 0 0 0 36 0 0 59 77 0 0 0 0 134 0 0 68 67 222 0 0 0 0 0 0 0 0 0 0 0</unk1>
    <display_bpm __type="u16" __count="12">160 0 0 0 0 0 0 0 0 0 0 0</display_bpm>
</music>
```

`music` is as follows:
- `idx` is the music ID.
- `genre`/`title`/`artist` are self explanatory.
- `fw_genre`/`fw_title`/`fw_artist` are the Japanese full width versions of - `genre`/`title`/`artist`. Generally the alphanumeric characters are uppercased for official songs but the game is not strict.
These fields are used to sort, therefore DO NOT USE HIRAGANA OR KANJI else your entry will not appear at the correct position in the songlist.
- `chara1`/`chara2` correspond to the `chara_id` in the character database XML.
- `folder` is the game version number.
- `cs_version` is the game version number for CS versioning.
- `categories` is a bitfield for categories
  - 0x0001: beatmania
  - 0x0002: IIDX
  - 0x0004: DDR
  - 0x0008: Gitadora
  - 0x0010: Mambo a Go Go
  - 0x0020: pop'n stage
  - 0x0040: Keyboarmania
  - 0x0080: Dance Maniax
  - 0x0100: bmIII
  - 0x0200: Toy's March
  - 0x0400: ee'mall (only ee'mall originals have this set)
  - 0x0800: jubeat
  - 0x1000: Reflec Beat
  - 0x2000: SDVX
  - 0x4000: BeatStream
  - 0x8000: Nostalgia
- `ha` is the hariai image. For example, songs that display jackets use the hariai image with a specific bit in the `mask` set. to display the jacket on the music select screen.
- `chara_x` and `chara_y` refers to the position of the character's face in the portrait. It's used to position the speech bubble and centering the image during the popout animation in the options screen.
- `unk1` is unknown data.
- `display_bpm` is an array of twelve values, consisting of the low ends of the bpm ranges for each chart followed by the highest ends. If both ends are the same, a constant bpm is displayed. If both values are negative, a question mark is displayed instead of the high value (e.g. Simonman songs). The popnhax parser won't take negative values, but the unsigned representations (=65535) in decimal work.

- `mask` is a bitfield that covers a lot of things
  - 0x00000008: Display a fake BPM range at the options screen, as defined by 'display_bpm'
  - 0x00000020: The alternate hariai image (set by using 0x800000) is a song jacket instead of a character portrait
  - 0x00000080: Seems to be related to locking away songs
  - 0x00010000: TV/J-Pop category flag is
  - 0x00080000: Easy chart flag
  - 0x00800000: Required for songs that show a hariai image on the music selection screen
  - 0x01000000: Hyper chart flag
  - 0x02000000: Ex chart flag
  - 0x04000000: Battle hyper chart flag
  - 0x08000000: Seems to be related to locking away songs
  - 0x80000000: Default for placeholder songs, so it's probably used to skip those songs
  - Anything else is undocumented here

`chart` is as follows:
- `idx` is the labeling for the difficulty: ep (Easy), np (Normal), hp (Hyper), op (Ex), bp_n (Battle Normal), bp_h (Battle Hyper).
- `folder` is the folder in `data/sd/` where the file can be found.
- `filename` is the base filename within `data/sd/<folder>`.
- `audio_param1`/`audio_param2`/`audio_param3`/`audio_param4` are something to do with the audio parameters. I believe `audio_param1` is BGM volume and `audio_param2` is keysound volume, or something like that. I haven't looked into this too much so consider it undocumented.
- `diff` is the difficulty of the chart. If set to 0 then the chart will be unselectable in-game (useful for normal and battle normal which are assumed to always be available by the game). The size of `diff` is 8 bits so its theoretical range is 0-255.
- `hold_flag` is whether the song should display as having hold notes or not on the music selection screen.
- `force_new_chart_format` forces popnhax to tell the game that the specified chart is in the new format (12 byte entries, allows for hold notes) instead of the old format (8 byte entries).
- `used_keys` is a bitfield that tells the game what notes were used in a chart. Only displayed when looking at easy charts on the music selection screen. You should see a pop'n music controller with buttons highlighted in the corner when selecting easy charts.
- `file_type` has two distinct usages. If `file_type` is <= 5 then it will look for `<filename>_<file_type>.ifs`. If `file_type` is > 5 then it'll look for `<filename>_diff.ifs`.

## Character database format

```xml
  <chara id="1500">
    <chara_id __type="str">wac_18b</chara_id>
    <flags __type="u32">0</flags>
    <folder __type="str">18</folder>
    <gg __type="str">gg_wac_18b</gg>
    <cs __type="str">cs_wac_18b</cs>
    <icon1 __type="str">cs_wac_18a</icon1>
    <icon2 __type="str">cs_wac_18b</icon2>
    <chara_xw __type="u16">128</chara_xw>
    <chara_yh __type="u16">75</chara_yh>
    <display_flags __type="u32">256</display_flags>
    <flavor>
      <phrase1 __type="str">ガジガジ</phrase1>
      <phrase2 __type="str">キューキュー</phrase2>
      <phrase3 __type="str">ニコニコ♪</phrase3>
      <phrase4 __type="str">トボトボ…</phrase4>
      <phrase5 __type="str">ウキャウキャ</phrase5>
      <phrase6 __type="str">グルグル</phrase6>
      <birthday __type="str">コノマエ</birthday>
      <chara1_birth_month __type="u8">1</chara1_birth_month>
      <chara2_birth_month __type="u8">0</chara2_birth_month>
      <chara3_birth_month __type="u8">0</chara3_birth_month>
      <chara1_birth_date __type="u8">1</chara1_birth_date>
      <chara2_birth_date __type="u8">0</chara2_birth_date>
      <chara3_birth_date __type="u8">0</chara3_birth_date>
      <style1 __type="u16">1</style1>
      <style2>
        <fontface __type="u32">5</fontface>
        <color __type="u32">6204672</color>
        <height __type="u32">28</height>
        <width __type="u32">19</width>
      </style2>
      <style3 __type="u16">28</style3>
    </flavor>
    <chara_variation_num __type="u8">1</chara_variation_num>
    <sort_name __type="str">ヒトリ</sort_name>
    <disp_name __type="str">ヒトリ</disp_name>
    <file_type __type="u32">0</file_type>
    <lapis_shape __type="str"></lapis_shape>
    <lapis_color __type="str"></lapis_color>
    <ha __type="str">ha_wac_18b</ha>
    <catchtext __type="str"></catchtext>
    <win2_trigger __type="s16">0</win2_trigger>
    <game_version __type="u32">18</game_version>
  </chara>
```

`chara` is as follows:
- `idx` is the character ID.
- `chara_id` is the base name of the character IFS.
- `flags` is a bitfield
  - 0x001: Character is dummied out
  - 0x002: Not playable
  - 0x004: Appears in the CS category
  - 0x008: Appears in the TV&Anime category
  - 0x010: Must be unlocked by unlocking at least one of their songs
  - 0x020: Can't use deco parts. Only used by Funassyi and doesn't even work after eclale.
  - 0x040: Must be unlocked by playing a round with the previous variation (unlocking P2 colors)
  - 0x080: Not sure, but seems to be used with the alternate portraits that were unlockable in Lapistoria
  - 0x200: Special color category, which was removed after Lapistoria
  - 0x400: Is from another BEMANI game, and thus appears in the BEMANI & GAMES category
  - 0x800: Is from a non-BEMANI Konami game, and thus appears in the BEMANI & GAMES category
- `folder` is the folder in `sd/tex/` where the character data is located.
- `gg`/`cs`/`icon1`/`icon2` are images associated with the character.
- `chara_xw `/`chara_yh` refers to the position of the character's face in the portrait. It's used to position the speech bubble and centering the image during the popout animation in the options screen.
- `display_flags` is (probably) a bitfield but I have not looked into this.
- `chara_variation_num` is the variation number of a character. This number increases for characters with a lot of alternative styles.
- `sort_name` and `disp_name` are self explanatory.
- `file_type` has two distinct usages. If `file_type` is <= 5 then it will look for `<filename>_<file_type>.ifs`. If `file_type` is > 5 then it'll look for `<filename>_diff.ifs`.
- `lapis_shape` is either blank or `dia`/`tear`/`heart`/`squ`.
- `lapis_color` is either blank or `blue`/`pink`/`red`/`green`/`normal`/`yellow`/`purple`/`black`.
- `ha` is the hariai image.
- `catchtext` is the catchphrase text that shows over top the image on the character selection screen.
- `win2_trigger` is undocumented.
- `game_version` is the source game version number.

`flavor` is as follows:
- `phrase1`/`phrase2`/`phrase3`/`phrase4`/`phrase5`/`phrase6` are the phrases a character can say.
- `birthday` is a string to be displayed in the birthday field on the character selection screen.
- `chara1_birth_month`/`chara2_birth_month`/`chara3_birth_month` and `chara1_birth_date`/`chara2_birth_date`/`chara3_birth_date` are the numeric values for the respective character's birth date and month.
- `style1` is undocumented.
- `style3` is undocumented.

`style2` is as follows:
- `fontface` is undocumented but changing it changes the font used for the character's text.
- `color` is the RGB values for the character's text. Example: `6204672` = `#5EAD00`.
- `width`/`height` are self explanatory.

# BM2DXFontScript format

BM2DXFontScript is the internal string formatting engine of the game.

Some of popnhax options use it as well.

It works a bit like printf so %s is our placeholder for the actual song/artist name (and since the function call is what it is, we cannot add new variables).

The different ways to alter texts are the following:
```
 [f:]   [/f]      anything other than 0 seems to break SJIS characters (maybe something to switch to another codepage for titles like Τέλος ?)
 [b:]   [/b]      Boldness
 [pos:] [/pos]    Position (seems to add a margin both left and right)
 [p:]   [/p]      Padding (space between letters)
*[c:]   [/c]      Color (rgb)
 [ol:]  [/ol]     OutLine
*[olc:] [/olc]    OutLine Color (rgb)
 [ds:]  [/ds]     Drop Shadow (adds a copy of same text behind, on bottom right)
*[dsc:] [/dsc]    Drop Shadow Color (rgb)
 [sx:]  [/sx]     Size x (text width) 0-100
 [sy:]  [/sy]     Size y (text height) 0-100
 [rz:]  [/rz]     Rotation along z axis (italic/slanted text)
 [sz:]  [/sz]     Size (looks much bigger than sx and sy)
 [a:]   [/a]      Unknown (alpha?)
 [r:]   [/r]      Unknown
 [br:]            Unknown (and the closing bracket [/br] doesn't exist.. line break? brightness?)
```

`*` indicates the value is rgb as hex (eg. [c:ff0000] for bright red)

other tags all take a single numerical value to set effect intensity

Unknown tags have no effect in the context of the songlist.. 

TODO: Fuzz another part of the code which uses the format and see the effect

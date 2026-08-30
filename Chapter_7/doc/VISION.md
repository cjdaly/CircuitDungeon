
In Chapter 7 we will design and implement a roguelike game for the PicoSystem

- using beads (https://github.com/gastownhall/beads) to track the work
- randomly generated levels
- new bitmaps / sprites - top-down / overhead view, not side
  - 16x16 uniform grid for terrain, objects, creatures, heroes (see doc/ART.md)
  - original art, hand-authored + procedural, grounded in the CC0 reference
    sets in sourceArt/ (0x72 tilesets, Project Utumno)
- more complex screen layout
  - text line at top and bottom (status / message ?)
  - map (about 2/3 of remainder)
  - inventory / stats (about 1/3)
  - resolved in doc/LAYOUT.md (Option G): 13×13 map viewport + a thin 32 px
    icon rail; full inventory/stats deferred to an optional toggle screen


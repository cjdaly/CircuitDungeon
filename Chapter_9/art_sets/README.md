# Room art sets (cd-342.35)

Several versions of the room backdrops live here side by side, so they can be
compared, on different boards at once if need be. A board only ever holds one:
`deploy.sh --art-set NAME` puts that set on it as `/art/rooms/`, with
`SET.txt` naming it, and the game prints it at start-up
(`Ch9 ready -- ... art=NAME`). The game code doesn't know sets exist.

| set | what it is |
|---|---|
| `drawn` | Hand-drawn in code by `tools/build_backdrops.py`; the original, kept current. **Covers every room** and is the base for the others. |
| `sdxl-repaint` | SDXL base 1.0 repainting the drawn art (img2img), snapped to the 16 DB16 colours, via `tools/gen_backdrops_ai.py`. Partial: just the rooms tried so far. |

## IP rule

The repo is public and the boards are gifts, so every set stays clear of other
people's intellectual property. A look or a mood is fine ("whimsical storybook,
wobbly shapes, candy stripes"); named characters, places, books, films, brands
or artists are not, in prompts or in the art. Prompts (`THEMES` in
`tools/gen_backdrops_ai.py`) describe a style in plain words, and the negative
prompt keeps creatures, characters and faces out. Every generated image is
looked at before it goes into a set; anything that resembles a known character
is thrown away, not edited.

## Layout

```
art_sets/<name>/set.json        name, description, base, made_by, rooms{file: {note}}
art_sets/<name>/rooms/*.bmp     120x120, 8-bit indexed, index i = DB16 colour i
```

A set may be **partial**: rooms it doesn't have come from its `base` set
(normally `drawn`). The tests check every set is complete once its base is
filled in, that every file is a real room and loads like the board loads it,
and that each file has a note in `set.json` saying where it came from.

## Using them

```
python3 Chapter_9/tools/art_set.py list                 # sets, how many rooms each
python3 Chapter_9/tools/art_set.py show sdxl-repaint    # which rooms are its own
Chapter_9/tools/deploy.sh --art-set sdxl-repaint        # put one on a board
python3 Chapter_9/tools/provision.py ... --art-set drawn # new unit; recorded in units/<id>.json
python3 Chapter_9/tools/art_set.py add sdxl-repaint "Sewing Nook" out.bmp --note "seed 2, strength 0.75"
```

`/usr/bin/python3 Chapter_9/tools/build_backdrops.py` rebuilds `drawn`. The
image-model setup for the generated sets is in `downloads/imagegen/` (not in
git; see its README).

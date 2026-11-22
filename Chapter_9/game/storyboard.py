# SPDX-License-Identifier: MIT
"""What happened, as comic beats: the one place the story becomes what's shown
-- cd-342.47.4, doc/ARCHITECTURE.md sec 4.

The hunt reports what just happened as a story.News (Hunt.news()). beats()
turns it into the beats the BeatPlayer plays (beats.py):

- each message becomes captions, two lines each (wrap());
- each cutscene it names is spliced in before its message: the escape
  (escape.py), with the box still shut under the captions before it, and the
  finale's (finale.CUTSCENES), with their own shots under the captions before
  and after;
- finding a critter shouts FOUND! first, with what it wants in a thought
  bubble over the first caption; bringing one home adds hearts.

Pure data, no displayio, so it runs under desktop Python
(tests/test_storyboard.py).
"""
import escape
import finale
from beats import Beat
from story import ESCAPE_SCENE, FOUND, RETRIEVED

_FOUND_BURST = "Found!"
_BONK_BURST = "Bonk!"
# Hearts either side of a critter that's coming home with you (screen px).
_HEARTS = (("heart", 56, 92), ("heart", 152, 92))

_BANNER_CHARS = 15  # Bangers on the round panel; tests check the real pixel widths


# Caption font (Bangers) advance widths in px, one per comic_fonts.GLYPHS character.
# tests/test_hunt.py (TestWrap) checks them against the BDF.
_CAPTION_GLYPHS = " !',.0123456789?ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_CAPTION_WIDTHS = (6, 7, 6, 6, 6, 12, 9, 12, 12, 12, 12, 13, 9, 14, 13, 12, 11, 11, 11, 12, 9, 9, 13, 12, 6, 8, 12, 8, 16, 12, 13, 10, 14, 12, 11, 10, 11, 10, 16, 11, 10, 11)
CAPTION_PX = 160  # widest caption line: keeps a two-line box's corners on the panel


def text_px(text):
    """Width of `text` in the caption font, upper-cased as it's drawn."""
    total = 0
    for ch in text.upper():
        i = _CAPTION_GLYPHS.find(ch)
        total += _CAPTION_WIDTHS[i] if i >= 0 else 0
    return total


def wrap(text, width=_BANNER_CHARS, px=CAPTION_PX):
    """Word-wrap into lines at most `width` characters and `px` pixels where possible."""
    lines = []
    line = ""
    for word in text.split(" "):
        longer = line + " " + word
        if line and (len(longer) > width or text_px(longer) > px):
            lines.append(line)
            line = word
        else:
            line = line + " " + word if line else word
    lines.append(line)
    return lines


def beats(news, icon=None):
    """The beats that show `news` (a story.News). `icon(name)` gives what a
    thought bubble draws for a scene_art name (SceneView.icon); without it the
    bubble gets the name."""
    cuts = dict(news.cutscenes)
    shown = []
    shot = _shot_before(cuts[min(cuts)]) if cuts else None
    for index, text in enumerate(news.messages):
        name = cuts.get(index)
        if name == ESCAPE_SCENE:
            shown.extend(escape.cutscene())
            shot = None
        elif name is not None:
            make, _before, after = finale.CUTSCENES[name]
            shown.extend(make(min(news.parade, finale.MAX_TOWER)))
            shot = after
        lines = wrap(text)
        # A caption holds two lines; anything longer runs on into the next.
        for i in range(0, len(lines), 2):
            shown.append(Beat(caption="\n".join(lines[i:i + 2]), shot=shot))
    if news.event == FOUND:
        if shown and news.want is not None:
            shown[0].thought = icon(news.want) if icon is not None else news.want
        shown.insert(0, Beat(burst=_FOUND_BURST))
    elif news.event == RETRIEVED and shown:
        shown[0].emanata = _HEARTS
    return shown


def bonk():
    """A move onto an edge with no exit at all."""
    return [Beat(burst=_BONK_BURST, shake=True)]


def _shot_before(name):
    if name == ESCAPE_SCENE:
        return escape.CALM
    return finale.CUTSCENES[name][1]

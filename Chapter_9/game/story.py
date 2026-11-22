# SPDX-License-Identifier: MIT
"""What the hunt reports, as plain data -- cd-342.47.4, doc/ARCHITECTURE.md.

The hunt (hunt.py) is the model; the views (nav_view.py, scene_view.py and
below) draw. This is everything that passes between them, so the views never
import the hunt:

- `Scene`: what the current room holds (Hunt.scene());
- `News`: what just happened (Hunt.news()), which storyboard.py turns into
  comic beats;
- `Escape`: the critter that just got out, for the escape cutscene;
- the names they use: events, box states, poses, where a lure sits.

No display code, so it runs under plain desktop Python.
"""

# What just happened (News.event).
FOUND = "found"
TOOK = "took"
RETRIEVED = "retrieved"
ESCAPED = "escaped"  # an episode began: play the escape (News.escape)
BURST = "burst"  # the finale began: every box popped
TOWER = "tower"  # the parade reached the batteries
CHARGED = "charged"  # home with the batteries: the ending

# The escape cutscene, as named in News.cutscenes (escape.py); the rest are
# finale.CUTSCENES's.
ESCAPE_SCENE = "escape"

# A present under the tree (Scene.boxes).
BOX_CLOSED = "closed"  # its critter hasn't got out yet
BOX_EMPTY = "empty"  # tipped over: its critter is out
BOX_HOME = "home"  # its critter is back, sitting on it

# How the critter looks in the room where it hides (Scene.pose).
HIDING = "hiding"
WAITING = "waiting"  # found, waiting for its lure

# Where a lure is drawn (Scene.lure_at): the middle of the room, big and
# bobbing (the default), or up on the Odd Corner's high shelf, small and
# still, so the batteries look out of reach.
SHELF = "shelf"


class Scene:
    """What the current room shows. Every field is None when absent.

    spot: scene_art name of the critter's hiding spot
    critter: its sprite id (critters.Critter.sprite), when it's in this room
    pose: HIDING (peeking out) or WAITING (found)
    lure: scene_art name of what's at the lure spot (the lure, or what hides it)
    lure_at: None for the middle of the room, or SHELF
    follower: sprite id of a critter following you home
    parade: the finale's critters following you, ((species, sprite id), ...),
        bottom of the tower first
    held: the item in hand
    boxes: under the tree (HOME only), ((species, BOX_*, sprite id), ...) in CAST order
    """

    def __init__(self, spot=None, critter=None, pose=None, lure=None, follower=None,
                 held=None, boxes=None, lure_at=None, parade=None):
        self.spot = spot
        self.critter = critter
        self.pose = pose
        self.lure = lure
        self.lure_at = lure_at
        self.parade = parade
        self.follower = follower
        self.held = held
        self.boxes = boxes


class Escape:
    """The critter that just got out, for the escape cutscene.

    `direction` is the way it bolts: the first step from the tree toward where
    it's hiding, so the cutscene is also a hint.
    """

    def __init__(self, species, sprite, name, direction):
        self.species = species
        self.sprite = sprite
        self.name = name
        self.direction = direction


class News:
    """What a move or tap just did, for storyboard.beats() to show.

    messages: the captions, in order, as plain strings
    event: one of the events above, or None
    cutscenes: ((message index, cutscene name), ...): each plays just before
        that message (ESCAPE_SCENE, or a finale.CUTSCENES name)
    escape: an Escape, when the escape cutscene is among them
    want: scene_art name of the lure, pictured in a thought bubble on FOUND
    parade: how many critters the finale has (the tower's height)
    """

    def __init__(self, messages, event=None, cutscenes=(), escape=None, want=None, parade=0):
        self.messages = list(messages)
        self.event = event
        self.cutscenes = tuple(cutscenes)
        self.escape = escape
        self.want = want
        self.parade = parade

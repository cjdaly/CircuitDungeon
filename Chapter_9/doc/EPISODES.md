# Christmas Critters — episodes, map gating, clues (DRAFT)

Living doc, started 2026-10-17 from Chris's direction. It widens the clue
idea in `STYLE.md` §5 and adds **per-critter map gating**. Proposals are
marked as such; decisions get marked **DECIDED**.

## 1. The game is a run of episodes

**DECIDED (Chris, 2026-10-17):** the map is one consistent house, but each
escaped critter opens only *part* of it. The whole map unlocks only in the
end game.

That makes the game a sequence of **episodes**, one per critter:

1. **Escape.** The cutscene from `STYLE.md` §4 plays and gives the first clue.
2. **Hunt.** The player explores the part of the map this episode opens,
   finds the critter and its lure item, and follows clues along the way.
3. **Home.** The critter goes back in its box (`STYLE.md` §6). The next box
   starts to rattle.

This settles `CRITTERS.md` open question 6 (escape timing): critters escape
**one at a time, in sequence**, not all at once.

## 2. Shape of an episode

**DECIDED (Chris, 2026-10-17):** an episode is **one path from the tree to
the critter, with dead-end side branches off it**:

```
Living Room (tree)
   |
1  room ------- false path (dead end)
   |
2  room ------- false path (dead end)
   |
3  room ------- Odd Corner (1-2 rooms)
   |
4  critter's hiding room
```

- **Length:** episode 1 is **3 moves**, a short warm-up. The rest are **4**,
  and at most one is **5**.
- **False paths:** rooms 1 and 2 each have a dead-end side branch. In the
  3-move episode 1, just room 1 does. The tree can have one too.
- **The favourite item** sits at the end of one of those dead-end side
  branches. It's never on the path itself and never in the Odd Corner's
  branch. At least one side branch is a pure false path, with no item.
- **A stuck door** can hold the item back until the critter is found.
  **DECIDED (Chris, 2026-11-02):** episode 1 does this, because the first
  playtest never found the yarn. Bumping it says `THE DOOR'S STUCK`; finding the
  critter gives `THE STUCK DOOR CREAKS OPEN!`. **DECIDED (Chris, 2026-11-03):**
  every episode holds its item back until the critter is found, using different
  unlocks, not all doors. Proposals are in `STORY.md`.
- **The Odd Corner** branches off **room 3** (room 2 in episode 1), so it's
  always far from the tree. **DECIDED: never directly off the tree**, which
  is also a whole-map test.
- **No loops:** each episode's open rooms form a tree, so there's one way to
  the critter and every dead end is really a dead end.
- **Every episode's wrong way ends in the same place**, the Odd Corner, with
  batteries just out of reach. So by the finale the player has seen them
  several times.
- **Sharing the Odd Corner:** it has only 4 edges, so at most 4 different
  rooms can sit next to it. With 5 episodes, at least two must share the
  same room 3, or reach it through one connecting room.
- All of these rules are tests in `tests/test_episodes.py`, so every
  episode is checked as soon as it's written.

*(Superseded first draft: a three-way fork at the tree into critter, lure
and wrong-way branches.)*

## 3. Exits: open, closed this time, none

**DECIDED (Chris, 2026-10-17):**
- There's always a visual signal of which directions are navigable and
  which are blocked. `nav_view`'s two marker states (pulsing green exit,
  dark static non-exit) already do this. "Closed this episode" shows as
  blocked; it doesn't need a third marker.
- Trying a blocked direction gets **comic feedback**:
  - **No exit at all:** a `BONK!` burst and a quick panel shake. This
    replaces today's red "can't go `<dir>`" toast.
  - **Closed this episode:** a short in-world reason that can double as a
    clue: `THE DOOR'S STUCK`, `TOO DARK DOWN THERE`,
    `SPARKY WOULDN'T GO IN THERE`.

## 4. Clues, widened

**DECIDED (Chris, 2026-10-17):** use clues where they make sense. A clue is
**text by default**, or an **image** when there's a suitable image or
scene. This replaces the strict "where at escape, what when found" split in
`STYLE.md` §5. That split is now just one pattern among several.

A clue has three parts: **when** it shows, **what form** it takes, and
**what it points at**.

| When | Example |
|---|---|
| Escape (end of cutscene) | caption `SPARKY LOVES TO SWIM!` |
| Which way it ran (escape beat 5) | the critter dashes for a particular edge. That's an image clue for free, if we want it to be honest |
| Entering a room | wet paw prints heading for the left edge; a feather on the floor |
| At a fork | tracks pointing at one exit, or an ambient animal's speech balloon: `WHOO! A ROBOT PUPPY WENT THAT WAY` |
| Bumping a closed exit | `SPARKY WOULDN'T GO IN THERE` |
| Tapping something | a chewed sock under the bed; a carrot top by the fridge |
| Finding the critter | thought bubble showing the lure item's icon |

**Image clues are cheap when they reuse the overlay kit:**
- **Tracks:** a dotted trail of paw-print glyphs drawn toward an exit edge.
  The comic motion-trail convention, and the best "which way" clue there is.
- **Dropped things:** a small 16x16 object in the scene.
- **Thought bubbles:** an item icon.

So text is the default and costs nothing, and image clues mostly come from
the emanata/icon sheet rather than new scenes.

## 5. The map is fluid

**DECIDED (Chris, 2026-10-17):** the map is **totally fluid**. It grows out
of the escape scenarios as we write them. The 10 rooms in
`rooms.make_world()` are a starting pile, not a plan. Rooms and exits get
added, moved or cut to fit each episode. The two things that stay fixed:

- **Consistency.** Every exit has a matching return exit, and every room is
  reachable from the Living Room. The existing `test_rooms.py` checks
  already enforce this.
- **The episode shape in §2** (one path with side branches, the Odd Corner
  off room 3, never next to the tree) is checked against the real map by
  tests.

**Worked example (illustrative only, roster and map not final):** Waddles
the robot penguin. Escape clue: `WADDLES WANTS TO SKATE!`

- **Critter branch:** Entryway -> Yard -> **Pond** (hiding). Wet flipper
  prints in the Yard point left.
- **Lure branch:** **Basement** (sardine tin on a shelf), reached by some
  route.
- **Wrong way:** Kitchen -> **the Odd Corner**. Dead end; batteries up on
  top of something, out of reach.
- **Closed this episode:** Yard -> Tree House and Yard -> Cave, with
  reasons when bumped.

## 6. End game: Christmas Eve chaos (`cd-342.6`)

**DECIDED (Chris, 2026-10-17):**
- After the last episode, **all the critters escape again at once** and go
  crazy, bouncing around the tree. You have to placate them.
- **The fix is the batteries in the Odd Corner**: the stash at the end of
  every wrong-way path, which you kept bumping into and couldn't quite
  reach. It doesn't have to be cookies; the Living Room already has
  Santa's cookies and milk.
- **Preferred: the critter tower.** You lead the critters to the Odd
  Corner, they climb on top of each other to reach the batteries, then
  carry them back to their boxes.
- **Fallback: comic-book logic.** You couldn't reach the stash before, and
  now you just can. Use this if the tower doesn't stage well on the
  device.

Batteries suit robot pets, and they hand the finale a motive for free: **it's
Christmas Eve and they're all running flat**. Cranky, glitchy robots are the
chaos. A fresh battery is the calm.

Proposed beats:

1. **Burst.** Every box pops at once, then several `POP!`s. The tree panel
   fills with critters bouncing off the panel rim (the circle makes a nice
   arena). Glitchy emanata: sparks, `!?`, low-battery icons. The whole map
   unlocks.
2. **Lead them.** The critters follow you room to room, a parade trailing
   in from the edge you came through. You already know the way to the Odd
   Corner, since every episode sent you there once.
3. **The tower.** In the Odd Corner, the critters stack one by one, each
   landing with a `HUP!`, until the top one reaches the batteries. A stack
   down the middle of the panel is the screen's tallest line, so 4–5
   critters at 32x32 (about 28px each, overlapping) fits. Optional small
   puzzle: tap them in the right order (biggest at the bottom). It's a
   stretch goal, not v1.
4. **Home.** Each critter carries a battery back and hops into its box.
   Hearts and a charged-up glow; lids drop; bows appear. Final ending
   (Santa? morning?) still open.

Rules that follow from this:
- The Odd Corner is **only** ever a wrong-way destination. It never holds
  a critter or a lure, so its first real use is the finale.
- Each visit, the batteries should be visibly *there*. Bumping toward them
  gets the comic feedback from §3 (`SO CLOSE!`, `JUST OUT OF REACH`), the
  "corner you keep bumping into".
- **Roster conflict:** the `CRITTERS.md` strawman has Flick's lure as "a
  fresh battery". Batteries now belong to the finale, so Flick needs a
  different lure.
- **Santa's cookies:** the joke is still optional. Tapping that plate gets
  `THOSE ARE FOR SANTA!`.

## 7. Data model sketch (for the beads)

- **`rooms.py`:** the graph stays the single truth. `World` gains an
  optional *gate*, the set of rooms open this episode. `move()` refuses an
  exit into a closed room and returns a distinct "closed" result so the UI
  can show the reason. `live_exits()` still drives the markers (closed shows as blocked), and
  a new `closed_exits()` lets a bump show its reason. With no gate set, behaviour is the same as now (end
  game, existing tests).
- **`episodes.py` (new, pure data):** one entry per critter:
  - which critter
  - the open rooms
  - the hiding room
  - the item and the room it's in
  - the closed-exit reason captions
  - the clues, each `(when, room, form, content)` with form text or image
- **Tests, mechanical:**
  - every episode's open set is connected and contains the Living Room
  - the hiding room and item room are reachable inside it and are different
  - the §2 shape: path length, no loops, false paths off rooms 1–2, the
    item in a side branch, the Odd Corner branch off room 3 and never next
    to the tree, and the Odd Corner never holding a critter or an item
  - every room and item named exists
  - every clue refers to a room in the open set
- **DECIDED (Chris, 2026-10-17): v1 hiding rooms are fixed** per episode.
  Randomizing them is a later stretch goal. Christmas is the deadline. The
  episode *order* is partly random, see §8.
- **Built (2026-10-17):** `game/episodes.py` and `tests/test_episodes.py`,
  plus the gate in `rooms.py`.

## 8. Episode order

**DECIDED (Chris, 2026-10-17): random middle.**
- The **cat is always first**: the shortest trips, so it doubles as the
  tutorial.
- The **reindeer is always last**: the roof leads into the finale.
- Dog, robot and squirrel are **shuffled** in between each playthrough.
- `episodes.make_order()` does this, with `FIRST`/`LAST` constants. Going
  fully random later is a one-line change.

The proposed default sequence, and what each episode adds:

| Slot | Critter | Hides | Lure | Adds |
|---|---|---|---|---|
| 1 | cat (always Chirpy) | Sun Porch, at the open window (3 moves) | yarn, Sewing Nook off the Dining Room | the basics: escape, text clue, false paths, the Odd Corner |
| 2–4 | dog | Yard | squeaky ball, Snow Fort off the Front Porch | a path the critter clears |
| 2–4 | robot | Basement | oil can, Garage off the Back Door | a dark room that lights up |
| 2–4 | squirrel | Tree House | walnuts, the dining table | an item you can see but have no reason to take; Flurry the owl |
| 5 | reindeer | the Roof | carrot, the snowman's nose in the Yard | a chain reaction in another room |

All of episodes 2–5 are 4 moves to the critter. The unlocks are in `STORY.md`.

**Episodes must not depend on their order.** Every episode is written to
work in any slot:
- **Each episode has its own open set.** Rooms opened in one episode don't
  stay open into the next. **DECIDED (Chris, 2026-11-03):** a door that was open
  last episode can simply be shut in this one, with no explanation needed.
- **New mechanics are explained the first time they appear**, with a
  one-time caption, not in a particular episode.
- **Story beats are tied to the episode's slot number, not to the
  critter.** For example, "it's getting late" is slot 4, whoever is loose.
- **Nothing one episode uses up is needed by another.** The snowman losing
  its nose is fine.

## 9. Episode 1: Chirpy (BUILT 2026-10-17, reshaped 2026-11-02)

**DECIDED (Chris, 2026-11-02):** the cat is always Chirpy (she/her), and the
episode is written for her. She likes the Living Room rug better than the
Laundry Room, and best of all sniffing fresh air at an open window. Tinsel and
Cinder are spares (`critters.SPARE`), maybe used later.

```
            Hallway (pure false path)
               |
Entryway x- Living Room -- Dining Room -- Kitchen -- Sun Porch (Chirpy)
 (closed)                       |            |    \
                           Sewing Nook   Odd Corner  x Basement (closed)
                             (yarn)
```

- **Path, 3 moves:** Living Room -> Dining Room -> Kitchen -> **Sun Porch**,
  where she's sniffing the air at the open window.
- **Home:** she curls up on the Living Room rug (`<NAME> CURLS UP ON THE RUG`).
- **Yarn:** in the **Sewing Nook**, up from the Dining Room (room 1's
  side branch), behind a door that's stuck until you've found her.
- **Pure false path:** the **Hallway**, up from the tree.
- **Odd Corner:** up from the **Kitchen** (room 2).
- **Closed exits, and what bumping them says:**
  - tree left, to the Entryway: `BRR! TOO COLD OUT THERE`
  - Kitchen down, to the Basement: `TOO DARK DOWN THERE`
- **Clues:**
  - at the escape: `<NAME> LOVES FRESH AIR!` (text)
  - entering the Dining Room, once the door is open: a yarn strand trailing in
    from the Sewing Nook, above (image; for now the text
    `YARN TRAIL! TAP THE TOP EDGE`)
  - entering the Kitchen: a breeze from the window (image; for now the text
    `YOU FEEL A CHILLY BREEZE`)
- **Clues must say which way, and can't be one-time.** First playtest
  (2026-11-02): Chris couldn't find the yarn and never went up from the Dining
  Room. A one-time `A STRAND OF YARN!` with no direction was too easy to miss.
  Room clues now show on every visit, and tapping the room repeats them; a clue
  pointing at the lure stops once it's held. `...GOES UP!` wasn't clear either:
  text clues should name the edge to tap.
- **New rooms:** Dining Room, Sewing Nook, Sun Porch. The Kitchen moved one room
  further from the tree, and the Laundry Room now hangs off the Basement.
- **Tested on the real map:**
  - the path is exactly those rooms
  - the tree shows up and right open, and left closed with its reason
  - the Kitchen stairs are closed with their reason
  - the Odd Corner is up from the Kitchen
  - the full loop works: fetch the yarn, then bring the cat home

## 10. Open: does the reindeer fly? (Chris, 2026-10-17)

**DECIDED FOR NOW (Chris, 2026-11-02): option (c)**, the fresh battery is what
makes the reindeer fly. Chris may revisit this once the whole story arc is
clearer.

Chris wasn't sure. A flying reindeer seems at odds with the critters having
to climb on each other to reach the batteries. Comic-logic options that
make it fit:

- **(a) It can't fly, and wants to more than anything.** "Wants to fly"
  stays its habit (it climbs to the roof to try). In the finale its antlers
  make the perfect bottom rung of the tower.
- **(b) It can fly, but its battery is too low.** It's the first thing that
  stalls when they all run flat, which is *why* they need the tower. Payoff:
  with a fresh battery the reindeer finally takes off, a natural last beat
  for the ending (a loop around the tree, or out to join a sleigh).
- **(c) Both.** It's never flown, and it sputters on the roof in its
  episode. The fresh battery from the finale is what finally gets it up.
  This turns the whole battery theme into the reindeer's little story arc.

Only the habit text and the episode-5 / finale beats depend on this. The
reindeer's episode isn't written yet.

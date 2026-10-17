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

## 2. Shape of an episode (proposal)

From the tree, the open map forks into **three kinds of branch**:

| Branch | Leads to | Depth |
|---|---|---|
| **Critter** | the room it's hiding in | 2–3 rooms |
| **Lure** | the room holding the item it wants | 1–3 rooms |
| **Wrong way** | always ends at **the Odd Corner** (§6) | 1–2 rooms |

That's Chris's "two directions passable and one wrong", applied to the two
halves of the fetch. Notes:

- **DECIDED (Chris, 2026-10-17): every episode's wrong way ends in the same
  place**: the Odd Corner, with batteries stashed just out of reach. Different
  episodes can reach it by different routes, since the map is fluid (§5).
  So the "wasted" trip plants the finale: by the end the player has seen
  the batteries out of reach several times. The branch can still carry a clue
  or an ambient animal on the way.
- Depth grows across the run. Early episodes are short with obvious clues;
  later ones go deeper (Yard -> Cave) and use subtler clues. So the house
  "grows" as you play, a light Metroidvania feel, without the map ever
  changing shape.
- Branches don't have to split right at the tree; a fork can come one room
  in. The rule that matters is that the critter and its lure are never in
  the same room (already a `CRITTERS.md` design rule).

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
- **The tree needs at least 3 exits** for the critter / lure / wrong-way
  fork. It has 2 today, so the first episode we write will add one.

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
  - every wrong-way branch ends at the Odd Corner, and that room
    never holds a critter or a lure
  - every room and item named exists
  - every clue refers to a room in the open set
- **DECIDED (Chris, 2026-10-17): v1 is fixed.** A fixed episode order and a
  fixed hiding room per episode. Randomizing either is a later stretch
  goal. Christmas is the deadline.

# Christmas Critters — roster

Draft for `cd-342.3`. The **Cast** section below is the current state; the
older strawman sections further down are kept for history and are marked
where they've been superseded.

## Cast (DECIDED 2026-10-17)

**Chris's calls:**
- **Five escaping critters, one per species:** a dog, a cat, a squirrel, a
  reindeer and a robot.
- **The sprite is random per playthrough** from that species' look-test
  variants.
- **Every sprite has its own name**, so the name comes with the rolled
  sprite. The species' lure and episode stay fixed.
- **Birds and the owl are wild.** They're scenery and ambience where they
  help fill out an area, never escapees. They still get names.
- **Pixel-doubled (`nn`) art.** `epx` stays only as a demo toggle.
- **Dogs:** old #2 is back in (2026-10-17), so there are three. Sparky and
  Woofer are Chris's names.

### Names (DECIDED 2026-10-17)

Rules used:
- Fit the sprite's colour or build.
- Lean robot-pun or Christmas.
- Short enough that `<NAME> ESCAPED!` is one Bangers caption line. All of
  these measure 129–165px against a ~170px band.
- No two escapees share a first letter, so they stay easy to tell apart
  in all-caps captions.
- Avoid trademarked characters (Rudolph, Frosty, K-9, AIBO). Santa's
  reindeer names come from the 1823 poem and are fine.

| # | Sprite | Name | Why | Alternates |
|---|---|---|---|---|
| 1 | dog, white with orange patches, perky ears | **Patch** | the patches | Biscuit, Domino |
| 2 | dog, red-orange all over | **Sparky** *(Chris)* | reddish; electric robot pun | — |
| 3 | dog, white/tan, the bulkiest dog | **Woofer** *(Chris)* | big, a subwoofer pun | — |
| 4 | cat, orange tabby | **Chirpy** *(Chris)* | — | — |
| 5 | cat, white with icy-blue shading | **Tinsel** | silvery and shiny | Sleet, Chrome |
| 6 | cat, black, glowing yellow eyes, the biggest cat | **Cinder** | fireplace soot, ember eyes | Static, Inky |
| 7 | squirrel, red-orange, bushy tail | **Nutmeg** | colour, nut pun, holiday baking | Rusty |
| 8 | squirrel, grey/blue-grey | **Acorn** | the squirrel's treasure | Chip (microchip pun), Pewter |
| 12 | reindeer, orange with red markings | **Vixen** | the poem's name, and fox-orange | Comet |
| 13 | reindeer, brown/grey, classic antlers | **Blitzen** | the poem's name; "blitz" = lightning, a robot fit | Dasher |
| 14 | robot, chunky grey-blue humanoid | **Rivet** | a riveted tin bot | Clunk, Tinker |
| 15 | robot, dark grey four-legged, red light on top | **Echo** | sonar/beeper feel | Beacon, Widget |
| 16 | robot, gold four-legged | **Jingle** | gold like a jingle bell | Brassy, Bell |
| 9 | *wild*: penguin | **Waddles** | carried over from the strawman | Tux |
| 10 | *wild*: puffin, bright beak | **Lolli** | lollipop beak | Pip |
| 11 | *wild*: snowy owl | **Flurry** | snowy | Hoot |

Numbers are the current 16-sprite numbering, the same as the demo and the
preview PNGs.

**Species details** (Chris, 2026-10-17: **a starting point, kept fluid**
like the map; adjust as episodes get written so everything fits):

| Species | Lure | Habit (where-clue) |
|---|---|---|
| dog | squeaky ball | loves the snow |
| cat | ball of yarn | loves warm, high places |
| squirrel | walnuts (not acorns, since one squirrel is *named* Acorn; nutcracker gag?) | loves to climb |
| reindeer | carrot | wants to fly |
| robot | oil can (**not** a battery; the finale owns those) | loves gadgets |

**In code:** `game/critters.py` has `CAST`, `WILD` and
`make_roster(choice=random.choice)`. `tests/test_critters.py` checks that:
- every sprite in the art list is cast or wild exactly once
- each sprite's species matches its art group
- names are unique and short enough for a caption
- no two species share an initial
- lures are distinct and none is a battery
- the roster rolls one critter per species

**Box colour:** with random sprites, "box colour = critter colour" can't
hold (orange cat vs orange squirrel, for one). Proposal: **one fixed
wrapping colour per species**, so the box still tells you who's missing
whichever sprite was rolled.

**Code impact:**
- The roster maps species to a sprite pool of candidate ids.
- A game-start roll picks one id per species. It's seeded per playthrough,
  so tests stay deterministic with a fixed seed.
- `critters.Critter` itself doesn't change.

> **Update 2026-09-21 — art first, names after.** The species below were my
> guesses. Chris's call: look through the source art for animated candidates
> (16x16, expanded to 32x32), test them on the device, choose the best, and
> only then name them and settle the rest. So treat the roster table as
> placeholder *roles* (a mix of pets, each with an item and hiding places), not
> as species commitments. Step 1 is the look-test — see *Look-test* below. Once it's settled it becomes the
real roster in `game/critters.py` (with a test that every room and item named
here exists in `rooms.py`), and the art briefs below feed `cd-342.5`.

The mechanic (from `critters.py`): each critter starts in its present box
under the Living Room tree, escapes to hide in another room, and comes back
only when the player is in that room **and** holding the item that critter
likes. So each critter needs: a hiding place, a preferred item, and a place
that item can be found.

## Look-test (step 1)

`game/critter_demo.py` browses the animated candidates (39 originally, culled to 15 on 2026-10-17) from DawnLike (CC-BY;
credited in the chapter README) at the real 32x32 size, on the real panel.
Desktop previews of the same sheets: `critter-candidates-nn.png` /
`critter-candidates-epx.png`. Survey notes:

- **Where the candidates come from:** DawnLike is the only source set with
  real animation for creatures (every character has a 2-frame idle, in paired
  `*0.png` / `*1.png` sheets). 0x72 DungeonTilesetII also animates (4-frame
  idle/run) but it's dungeon monsters — goblins, imps, zombies — and
  MedievalFantasy is human knights/kings; neither has pets. Kenney Tiny
  Dungeon is static. The Adafruit tutorial sheet has a robot face and Blinka
  but only 6 static 16x16 tiles, no animation, license unchecked — skipped.
- **Groups in the demo:** dog ×4, cat ×5, rodent ×3, bunny? ×4 (they could
  as easily be jackalopes), bird/penguin ×5, owl ×4, bat ×3, reindeer ×2,
  sheep ×1, toy-ish robot ×6, snow ×2.
- **Expansion:** every source frame is 16x16; `nn` doubles each pixel
  (chunky, faithful), `epx` is Scale2x smoothing (rounder diagonals, same
  15-colour palette). Tap on the device flips between them — which looks
  better at 32x32 on that round panel is one thing to decide.

**What to write down while browsing** (the serial console echoes each pick):
your favorites (5 or so), which of `nn`/`epx` you prefer, anything that
doesn't read at true size (bottom sprite, straddling dark/light), and whether
the animation speed feels right. Also: do you want a *cohesive set* (e.g. all
recolored to match) rather than the best individual sprites? Recoloring is
cheap since every sheet shares one palette.

### Cull (Chris, 2026-10-17, DONE: 39 -> 16)

Numbers below are the **old** `1`–`39` demo numbering. After the rebuild, the demo and preview PNGs number the 15 survivors `1`–`15` in the same order.

| Group | Keep | Drop |
|---|---|---|
| dog (1–4) | 1, 2, 3 (2 re-added later) | 4 |
| cat (5–9) | 6, 7, 9 | 5, 8 |
| rodent (10–12) -> **squirrel** | 10, 11 | 12 |
| bunny (13–16) | — | all (13–16) |
| bird (17–21) | 18, 19 | 17, 20, 21 |
| owl (22–25) | 23 | 22, 24, 25 |
| bat (26–28) | — | all (26–28) |
| reindeer (29–30) | 29, 30 | — |
| sheep (31) | — | 31 |
| robot (32–37) | 33, 34, 35 | 32, 36, 37 |
| snow (38–39) | — | all (38–39) |

Rebuilt 2026-10-17. The sheets are now 16 candidates, 38KB each in flash
(down from 87KB).

Then old #2 (the red-orange dog, now Sparky) came back in, which makes 16.

Current numbering: 1–3 dogs, 4–6 cats, 7–8 squirrels, 9–10 birds, 11 owl,
12–13 reindeer, 14–16 robots.

**Strawman fallout:**
- Two strawman critters lost their species: **Bun** (bunnies dropped) and
  **Flick** (bats dropped). Flick's battery lure was already taken by the
  finale anyway.
- Still covered: **Sparky** (dog), **Mittens** (cat), **Waddles**
  (bird 8 is the penguin-ish one).
- New options for those slots: squirrel, owl, reindeer, robot.

So the roster table below is due for a rewrite once the cast is picked
from these 15.

## Showing movement

The candidate art is 2-frame and side-on only (DawnLike's every character has
exactly two frames; 0x72 II has 4-frame idle/run but only dungeon monsters,
front-facing, and MedievalFantasy is 8–22-frame humans at 64–128px — none are
pets). So movement is layered from cheap parts, in `game/walk.py`:

- **Slide** between waypoints at a constant speed.
- **Mirror** for direction: the sprites face left, so heading right sets
  `TileGrid.flip_x` (free — no mirrored sheet, no extra memory). Facing sticks
  through vertical legs and pauses. Front-facing critters (owls, bats,
  penguins, robots) don't visibly change when mirrored; they just hop.
- **Step**: flip the two frames faster while moving (0.2s) than at rest (0.5s)
  and add a 1–2px hop in time with the steps, so it reads as walking, not
  gliding.
- **More frames if a favorite needs them:** derive in-betweens from the two we
  have, or hand-author extra frames just for the 4–5 winners (Ch7-style
  ASCII grids). Not needed until something looks wrong.

Walk mode in `critter_demo.py` (tap the bottom half of the screen) shows a
critter patrolling a rectangle over a floor with a light rug. Things to judge
on the device: does the cadence/bob read as walking; does any critter
moonwalk (drawn facing right — tell me which); is 40 px/s a good pace;
do the outlines survive the dark floor and the light rug. The tuning
constants are at the top of `critter_demo.py`.

## Design rules I followed

- **Robot pets** (per the design sketch), so each has one robot-ish trait
  that shows in its 32x32 silhouette.
- **Five critters** — a nice number of presents under the tree, a
  short-enough session for an ornament-sized game, and each one gets a
  visibly different silhouette at 32x32.
- **Two-part fetch stays real:** a critter's item is never in a room where
  that critter can hide, so the player can't get both in one stop.
- **Each critter has two possible hiding rooms**; which one it uses is picked
  at escape time (replayability; also means the item-then-critter order isn't
  memorizable). Two critters shouldn't hide in the same room at once.
- **Item rooms are spread out** so a run makes the player walk the whole
  house, not just the Yard cluster.
- **Box color = critter color.** Each present has its own wrapping-paper
  color, and the critter matches it — the only "hint" that needs no text.

## The roster (SUPERSEDED 2026-10-17 by *Cast* above)

| Critter | What it is | Box | Likes (item) | Item found in | Hides in (either) |
|---|---|---|---|---|---|
| **Sparky** | robot puppy, wagging antenna-tail | red | a squeaky ball | Kids' Bedroom | Yard, Tree House |
| **Mittens** | robot kitten, LED whiskers | green | a ball of yarn | Entryway (basket of scarves) | Basement, Kids' Bedroom |
| **Bun** | robot bunny, spring-loaded ears | gold | a carrot | Kitchen | Tree House, Cave |
| **Waddles** | robot penguin, wind-up key on its back | blue | a tin of sardines | Basement (pantry shelf) | Pond, Yard |
| **Flick** | robot bat, flickering-lamp eyes | purple | a fresh battery (**conflict**: batteries are now the finale, see `EPISODES.md` §6; needs a new lure) | Bedroom (bedside clock) | Cave, Basement |

Distance from the start (Living Room), in room moves: Kitchen/Entryway 1;
Basement/Bedroom/Yard 2; Kids' Bedroom/Pond/Tree House/Cave 3. Items are 1–3
moves out and hiding rooms are 2–3 moves out.

Per-retrieval cost, in room moves from the start (the critter returns to its
box on success, so there's no carry-back): grabbing the **item first** takes
3–7 moves; **finding the critter first, then fetching the item** takes 7–13
(worst case: Waddles hiding at the Pond, sardines in the Basement). That's a
reasonable spread for an ornament-sized game and rewards guessing the item
first — which is what the thought-bubble question below is really about.

### Fit with the room graph

- Every item room and hiding room above is a real room in `rooms.make_world()`.
- No item shares a room with its own critter's hiding options (checked by
  hand; the real-roster test will check it mechanically).
- Role of each room: **item only** — Kitchen (carrot), Entryway (yarn),
  Bedroom (battery); **hiding only** — Yard, Pond, Tree House, Cave;
  **both** — Basement (sardines; Mittens/Flick may hide there) and Kids'
  Bedroom (ball; Mittens may hide there); **neither** — Living Room, which is
  the start and holds the boxes.

### Art briefs (for `cd-342.5`, 32x32)

- **Sparky** — floppy ears, tongue, a little antenna for a tail. Red accents.
- **Mittens** — pointed ears, glowing whisker dots. Green accents.
- **Bun** — tall ears with a spring/coil joint. Gold accents.
- **Waddles** — round body, flippers, key on the back. Blue accents.
- **Flick** — folded wings, two bright eyes (works well in the dark Cave/
  Basement). Purple accents.
- **Items** (16x16, scenery scale): squeaky ball, yarn ball, carrot, sardine
  tin, battery. Each must read at 16x16 and be distinct from room decor.

## Open questions for you

> **Update 2026-10-17:** `EPISODES.md` settles or reshapes several of these.
> - **Q6:** critters escape one at a time, one episode each, with map
>   gating per critter.
> - **Q3 and Q5:** folded into a wider clue system, text by default and an
>   image when one fits. The thought bubble (Q3a) and the "rustling" cue
>   (Q5) are both clue patterns in it.
> - **Q4:** with one critter loose at a time, one held item is the natural
>   default.
> - **The roster table:** "hides in (either)" becomes one fixed hiding room
>   per episode for v1. Item and hiding rooms must sit inside that
>   episode's open map.

1. **Names and species** — keep, swap, or add? (A reindeer or snowman
   critter would be very on-theme; I didn't include one because it'd
   compete with the tree/ornament visuals. Say if you want one.)
2. **Count** — 5 fine, or fewer for a first playable (3 is enough to prove
   the loop) with the rest added later?
3. **How does the player learn what a critter likes?** Options: (a) the
   critter shows a little thought-bubble icon of its item when you find
   it; (b) the empty box has a tag showing the item; (c) trial and error
   (drop a wrong item and it ignores you). I lean toward (a) — it needs no
   text and works on a 240px screen.
4. **Inventory size** — carry one item at a time (more backtracking, more
   puzzle) or two (more forgiving)? I lean toward one, since 5 items in a
   10-room house is already plenty of walking. This is the main input to
   `cd-342.4`.
5. **Hint before finding** — `CritterRoster.hiding_in()` can drive a
   "something's rustling in here" cue when you enter the right room. Yes?
   It also gives the ornament/idle mode something to do later.
6. **Escape timing** — all at once when the game starts, or one at a time
   over the session (e.g. every few minutes, so the first one is
   discoverable quickly)? That's the `cd-342.4` trigger question; the
   roster doesn't need it, but it affects how many critters are worth having.

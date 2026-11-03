# Christmas Critters — the story, start to finish (DRAFT)

The whole arc on one page, started 2026-11-03 so Chris can react to it before
episodes 2–5 get written. Details live in `EPISODES.md` (episodes, finale) and
`STYLE.md` (the look). **DECIDED** marks Chris's calls; everything else is a
proposal. Chris OK'd the unlocks and the ending for now (2026-11-03), subject to
playtesting, and wants a name on each board.

## The premise

It's Christmas Eve, and you're the last one up. Under the tree are five wrapped
presents, each holding a robot pet, and their batteries are running low. Low
batteries make robots twitchy, so they keep breaking out of their boxes. You have
to get them all back before morning. You're never drawn: the screen is what you
see, and the pets talk to you.

## The arc

| When | What happens | What it adds to the story |
|---|---|---|
| **Episode 1: Chirpy** (always first) | She's gone for fresh air on the Sun Porch. She curls up on the rug when she's home | How the game works. You first see the batteries in the Odd Corner, out of reach |
| **Episodes 2–4: dog, robot, squirrel** (shuffled) | Each hunt opens a different part of the house and yard | The night wears on. Each pet is glitchier than the last, and each wrong turn ends at those batteries |
| **Episode 5: the reindeer** (always last) | It's on the Roof trying to fly, and it can't: it sputters and drops | The longest trip. It's the clearest sign yet that the batteries are failing |
| **Finale** | Every box pops at once. The pets go haywire around the tree and the whole house opens | The thing you kept bumping into is the answer: the batteries |
| **The tower** | You lead the parade to the Odd Corner. They climb on each other and reach the batteries | Why the batteries were always just out of reach |
| **Home** | Each pet carries a battery back and hops in its box. Lids drop, bows appear | The calm after the chaos |
| **Ending** | The reindeer, freshly charged, finally lifts off for a lap around the tree. Then the plate of cookies turns out to be empty | **DECIDED for now:** the battery makes it fly. Santa came, and you never saw him |

**Keeping time:** a caption opens each episode with the hour, tied to its slot and
not to the pet: `9 PM`, `10 PM`, `11 PM`, `NEAR MIDNIGHT`, `MIDNIGHT`. That gives
the shuffled middle a sense of the night passing.

**The ending (proposal).** No Santa sprite is needed, which suits first person and
saves art. All night, tapping the plate says `THOSE ARE FOR SANTA!`. After the
reindeer lands, the plate holds only crumbs and a note: `THANKS! NICE ROBOTS.`
Then the game fades into ornament mode, with the tree lit and the boxes wrapped,
so the gift stays an ornament after it's been played. A tap offers another
playthrough.

**A personal touch (DECIDED, Chris 2026-11-03).** These are gifts, so the game ends
with `MERRY CHRISTMAS,` then `<NAME>!`, using `PLAYER` in the board's
`settings.toml`. Without it, the game just says `MERRY CHRISTMAS!`.

## Unlocks: you can't get the lure until you find the pet

**DECIDED (Chris, 2026-11-03):** every episode holds its lure back until you've
found the pet, and they shouldn't all be stuck doors. The pet should cause the
unlock, in a way that fits it. All five work as plain text first, and pictures
can come later.

| Pet | Before you find it | When you find it | The kind of unlock |
|---|---|---|---|
| **Chirpy** (built) | `THE DOOR'S STUCK` | `THE STUCK DOOR CREAKS OPEN!` | A door |
| **Dog** in the Yard, ball in a new Snow Fort | A drift blocks the way: `THE SNOW'S TOO DEEP` | `DIG DIG DIG!` It tunnels through, and paw prints show you where | The pet clears a path |
| **Robot** in the Basement, oil can in a new Garage | The Garage is open but pitch black: `TOO DARK TO FIND ANYTHING` | It's been chewing on the fuse box. `ZAP! THE LIGHTS COME ON` | A room changes, and nothing is blocked |
| **Squirrel** in the Tree House, walnuts on the dining table | A bowl in plain sight: `WALNUTS. YOU'RE NOT HUNGRY` | `WALNUTS ON THE DINING TABLE!`, and now you can take them | You need a reason |
| **Reindeer** on the Roof, carrot in the Yard | The snowman's nose: `HE NEEDS THAT NOSE` | It sputters and lands hard. `WHUMP! SNOW SLIDES OFF!` It flattens the snowman, leaving the carrot on top | A chain reaction in another room |

Why these: the squirrel brings back the "oh, I saw that earlier!" moment, since you
may already have walked past the walnuts. The reindeer's failed takeoff sets up the
ending. The dog and the robot show the same idea, of the pet changing the world,
in two very different ways.

**Spare ideas**, if one of these doesn't work:
- **A wild animal has it:** Flurry the owl has the walnuts in her nest and only
  gives them up once she sees you've found the squirrel.
- **The pet gives you a tool:** a key from the dog's mouth, or the robot's flashlight.
- **A sound:** a squeak you can only hear once the dog has perked up and led you to it.

**What this means for the code.** It comes down to two mechanisms, in
`episodes.Unlock`. Either an exit opens (door, drift), or a lure in an open room
becomes takeable, with different text before and after (lights, walnuts, snowman).
Each resets at the next episode, so the shuffled order still doesn't matter.

**What this means for the map.** It stays fluid. Episodes 2–5 added the Front
Porch, Front Walk, Snow Fort, Back Door, Garage, Cellar Door, Attic and Roof. Rooms
open by name, so a room next to the Odd Corner can't be open in an episode that
reaches the Corner some other way, or it makes a loop. That's why the walnuts are
on the dining table and not in the Kitchen. Doors that were open in one episode
can be shut in the next, and that needs no explanation (Chris, 2026-11-03).

The map doesn't have to be logical, Zork-style, but not too much (Chris,
2026-11-03). The Odd Corner is the main case: you can reach it from the Kitchen,
the Attic, the Front Walk or the Cellar Door. Every exit still has a return exit.

## Still open

1. **Who's "you"?** I've left it as nobody in particular. A kid sneaking down, or a
   parent wrapping presents, would each give the captions a different voice.
2. **The tower:** the finale's preferred version needs the most new art and code of
   anything here. `EPISODES.md` §6 keeps a simpler fallback if time runs short.
3. **Pond and Cave:** nothing above uses them. Keep them as locked flavour, or cut them?

# SPDX-License-Identifier: MIT
# Off-device tests for game/hunt.py, played against the real map and episodes.
#
#   python3 Chapter_9/tests/test_hunt.py

import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critters  # noqa: E402
import episodes  # noqa: E402
import hunt  # noqa: E402
import rooms  # noqa: E402
from rooms import DOWN, LEFT, RIGHT, UP  # noqa: E402

_GAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "game")

# Widths available on the round panel, in pixels, from nav_view's layout.
_CAPTION_PX = 160  # keeps a two-line caption box's lower corners on the panel
_ROOM_NAME_PX = 160  # the panel's width, inside its ink ring, at the room name's top


def _advance_widths(filename):
    """{character: advance width in pixels} from a font file in game/fonts."""
    with open(os.path.join(_GAME, "fonts", filename)) as f:
        found = re.findall(r"ENCODING (\d+).*?DWIDTH (\d+)", f.read(), re.S)
    return {chr(int(code)): int(width) for code, width in found}


_TITLE = _advance_widths("luckiestguy-spaced45-24.bdf")
_CAPTION = _advance_widths("bangers-spaced45-24.bdf")


def _px(text, font):
    """Width of `text` as drawn: upper-cased, and every character must exist."""
    return sum(font[c] for c in text.upper())


def first_choice(options):
    return options[0]


class HuntCase(unittest.TestCase):
    def setUp(self):
        self.world = rooms.make_world()
        self.roster = critters.make_roster(choice=first_choice)
        self.hunt = hunt.Hunt(self.world, self.roster, order=["cat"])
        self.opening = self.hunt.start()
        self.cat = self.hunt.critter

    def walk(self, *directions):
        messages = []
        for direction in directions:
            self.assertTrue(self.world.move(direction), direction)
            messages = self.hunt.entered()
        return messages

    def find_cat(self):
        """Find her, which opens the yarn door, and walk back to the Dining Room."""
        self.walk(RIGHT, RIGHT, RIGHT)
        self.hunt.tapped()
        self.walk(LEFT, LEFT)


class TestEscape(HuntCase):
    def test_first_episode_is_the_cat(self):
        self.assertEqual(self.hunt.episode.species, "cat")
        self.assertEqual(self.cat.state, critters.HIDING)
        self.assertEqual(self.cat.location, "Sun Porch")

    def test_opening_announces_the_escape_and_the_clue(self):
        self.assertEqual(
            self.opening, ["9 PM", "Chirpy escaped!", "Chirpy loves fresh air!"]
        )

    def test_only_this_episodes_rooms_are_open(self):
        behind_the_door = {self.hunt.episode.lure_room}
        self.assertEqual(self.world.gate, set(self.hunt.episode.open_rooms) - behind_the_door)
        self.assertNotIn(LEFT, self.world.live_exits())

    def test_tapping_at_the_tree_repeats_the_clue(self):
        self.assertEqual(self.hunt.tapped(), ["Chirpy loves fresh air!"])


class TestStuckDoor(HuntCase):
    def test_the_door_starts_shut_with_its_reason(self):
        self.walk(RIGHT)
        self.assertNotIn(UP, self.world.live_exits())
        self.assertEqual(self.hunt.bumped(UP), "The door's stuck")

    def test_no_trail_points_at_a_stuck_door(self):
        self.assertEqual(self.walk(RIGHT), [])
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_finding_the_critter_opens_it(self):
        self.walk(RIGHT, RIGHT, RIGHT)
        self.assertEqual(
            self.hunt.tapped(), ["Chirpy wants the yarn", "The stuck door creaks open!"]
        )
        self.assertEqual(self.hunt.event, hunt.FOUND)
        self.walk(LEFT, LEFT)
        self.assertIn(UP, self.world.live_exits())

    def test_it_only_creaks_open_once(self):
        self.walk(RIGHT, RIGHT, RIGHT)
        self.hunt.tapped()
        self.assertEqual(self.hunt.tapped(), ["Chirpy wants the yarn"])
        self.assertIsNone(self.hunt.event)  # already found: no second FOUND!

    def test_an_episode_without_an_unlock_has_its_lure_open_from_the_start(self):
        cat = episodes.EPISODES["cat"]
        self.addCleanup(setattr, cat, "unlock", cat.unlock)
        cat.unlock = None
        world = rooms.make_world()
        game = hunt.Hunt(world, critters.make_roster(choice=first_choice), order=["cat"])
        game.start()
        world.move(RIGHT)
        self.assertIn(UP, world.live_exits())
        self.assertEqual(game.entered(), ["Yarn trail! Tap the top edge"])


class TestFindingThings(HuntCase):
    def test_lure_room_says_nothing_its_lure_is_drawn(self):
        self.find_cat()
        self.assertEqual(self.walk(UP), [])
        self.assertEqual(self.hunt.scene().lure, "ball of yarn")

    def test_tapping_the_lure_takes_it(self):
        self.find_cat()
        self.walk(UP)
        self.assertEqual(self.hunt.tapped(), ["Got the ball of yarn!"])
        self.assertEqual(self.hunt.held, "ball of yarn")
        self.assertEqual(self.hunt.event, hunt.TOOK)

    def test_lure_room_goes_quiet_once_taken(self):
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        self.assertEqual(self.walk(DOWN, UP), [])
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_critter_without_the_lure_says_what_it_wants(self):
        self.assertEqual(self.walk(RIGHT, RIGHT, RIGHT), [])  # she's drawn, peeking
        self.assertEqual(self.hunt.tapped()[0], "Chirpy wants the yarn")
        self.assertEqual(self.hunt.event, hunt.FOUND)
        self.assertEqual(self.cat.state, critters.HIDING)

    def test_every_critter_says_its_own_name(self):
        self.cat.name = critters.SPARE[0][1]
        self.walk(RIGHT, RIGHT, RIGHT)
        self.assertEqual(self.hunt.tapped()[0], "Tinsel wants the yarn")

    def test_empty_room_tap(self):
        self.walk(UP)
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_odd_corner_shows_the_batteries_but_they_stay_out_of_reach(self):
        messages = self.walk(RIGHT, RIGHT, UP)
        self.assertIn("Batteries! Just out of reach", messages)
        self.assertEqual(self.hunt.tapped(), ["So close!"])
        self.assertIsNone(self.hunt.held)

    def test_yarn_clue_says_which_way_on_every_visit_once_the_door_opens(self):
        self.find_cat()
        self.assertEqual(self.walk(LEFT, RIGHT), ["Yarn trail! Tap the top edge"])
        self.assertEqual(self.walk(LEFT, RIGHT), ["Yarn trail! Tap the top edge"])

    def test_tapping_a_clue_room_repeats_its_clue(self):
        self.find_cat()
        self.assertEqual(self.hunt.tapped(), ["Yarn trail! Tap the top edge"])

    def test_yarn_clue_stops_once_the_yarn_is_held(self):
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        self.assertEqual(self.walk(DOWN), [])
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_breeze_clue_stays_after_taking_the_yarn(self):
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        self.assertEqual(self.walk(DOWN, RIGHT), ["You feel a chilly breeze"])


class TestBumps(HuntCase):
    def test_closed_exit_gives_the_episodes_reason(self):
        self.assertEqual(self.hunt.bumped(LEFT), "brr! too cold out there")

    def test_no_exit_at_all_gives_no_reason(self):
        self.assertIsNone(self.hunt.bumped(DOWN))


class TestBringingItHome(HuntCase):
    def fetch(self):
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        self.walk(DOWN, RIGHT, RIGHT)

    def test_tapping_with_the_lure_brings_it_along(self):
        self.fetch()
        self.assertEqual(self.hunt.tapped(), ["Chirpy follows you home!"])
        self.assertEqual(self.hunt.event, hunt.RETRIEVED)
        self.assertEqual(self.cat.state, critters.RETURNED)
        self.assertIsNone(self.hunt.held)
        self.assertEqual(self.hunt.stage, hunt.GOING_HOME)

    def test_tapping_while_going_home_is_a_reminder(self):
        self.fetch()
        self.hunt.tapped()
        self.assertEqual(self.hunt.tapped(), ["Chirpy is with you. Go home!"])

    def test_old_rooms_stay_quiet_on_the_way_home(self):
        self.fetch()
        self.hunt.tapped()
        self.assertEqual(self.walk(LEFT), [])

    def test_reaching_the_tree_finishes_the_episode(self):
        self.fetch()
        self.hunt.tapped()
        messages = self.walk(LEFT, LEFT, LEFT)
        self.assertEqual(messages[0], "Chirpy curls up on the rug")
        self.assertEqual(self.hunt.stage, hunt.DONE)
        self.assertIsNone(self.world.gate)
        self.assertEqual(self.hunt.tapped(), ["Merry Christmas!"])

    def test_passing_through_the_tree_while_hunting_does_nothing_special(self):
        self.walk(RIGHT, LEFT)
        self.assertEqual(self.hunt.stage, hunt.HUNTING)


class TestEpisodeSequence(unittest.TestCase):
    def test_next_episode_starts_at_the_tree_with_its_own_gate(self):
        world = rooms.make_world()
        roster = critters.make_roster(choice=first_choice)
        game = hunt.Hunt(world, roster, order=["cat", "dog"])
        game.start()
        for direction in (RIGHT, RIGHT, RIGHT):
            world.move(direction)
            game.entered()
        game.tapped()  # found her: the yarn door opens
        for direction in (LEFT, LEFT, UP):
            world.move(direction)
            game.entered()
        game.tapped()  # the yarn
        for direction in (DOWN, RIGHT, RIGHT):
            world.move(direction)
            game.entered()
        game.tapped()
        for direction in (LEFT, LEFT):
            world.move(direction)
            game.entered()
        world.move(LEFT)
        messages = game.entered()

        self.assertEqual(
            messages,
            ["Chirpy curls up on the rug", "10 PM", "Patch escaped!", "Patch loves the snow!"],
        )
        self.assertIs(game.episode, episodes.EPISODES["dog"])
        dog = game.episode
        self.assertEqual(world.gate, set(dog.open_rooms) - {dog.lure_room})
        self.assertEqual(game.stage, hunt.HUNTING)
        self.assertIsNot(episodes.EPISODES["cat"], dog)

    def test_the_default_order_is_every_critter_cat_first_reindeer_last(self):
        game = hunt.Hunt(rooms.make_world(), critters.make_roster(choice=first_choice))
        self.assertEqual(sorted(game._order), sorted(episodes.EPISODES))
        self.assertEqual(game._order[0], "cat")
        self.assertEqual(game._order[-1], "reindeer")


class TestFontFiles(unittest.TestCase):
    def test_glyph_list_matches_both_font_files(self):
        with open(os.path.join(_GAME, "comic_fonts.py")) as f:
            glyphs = re.search(r'GLYPHS = "(.*)"', f.read()).group(1)
        self.assertEqual(set(_TITLE), set(glyphs))
        self.assertEqual(set(_CAPTION), set(glyphs))


def _route(world, goal):
    """The live exits to walk from the current room to `goal`, or None."""
    came_from = {world.current: None}
    frontier = [world.current]
    while frontier:
        name = frontier.pop(0)
        if name == goal:
            steps = []
            while came_from[name] is not None:
                name, direction = came_from[name]
                steps.append(direction)
            return steps[::-1]
        for direction, dest in world.get(name).exits.items():
            if world.is_open(dest) and dest not in came_from:
                came_from[dest] = (name, direction)
                frontier.append(dest)
    return None


class TestWholeGame(unittest.TestCase):
    """Plays every episode the way a player has to, in any order."""

    ORDERS = (
        ["cat", "dog", "robot", "squirrel", "reindeer"],
        ["cat", "squirrel", "robot", "dog", "reindeer"],
        ["cat", "robot", "dog", "squirrel", "reindeer"],
    )

    def setUp(self):
        self.world = rooms.make_world()
        self.game = hunt.Hunt(self.world, critters.make_roster(choice=first_choice))

    def go(self, goal):
        steps = _route(self.world, goal)
        self.assertIsNotNone(steps, "can't reach {} from {}".format(goal, self.world.current))
        messages = []
        for direction in steps:
            self.assertTrue(self.world.move(direction))
            messages = self.game.entered()
        return messages

    def play_episode(self):
        episode = self.game.episode
        self.go(episode.hide_room)
        self.game.tapped()  # found: the lure can now be reached
        self.go(episode.lure_room)
        self.assertEqual(self.game.tapped()[0], "Got the {}!".format(self.game.critter.preferred_item))
        self.go(episode.hide_room)
        self.game.tapped()
        self.assertEqual(self.game.stage, hunt.GOING_HOME)
        return self.go(critters.HOME)

    def test_every_order_can_be_finished(self):
        for order in self.ORDERS:
            with self.subTest(order=order):
                self.setUp()
                self.game._order = list(order)
                self.game.start()
                for _ in order:
                    self.play_episode()
                self.assertEqual(self.game.stage, hunt.DONE)
                self.assertIsNone(self.world.gate)

    def test_the_hour_moves_on_with_each_episode(self):
        self.game._order = list(self.ORDERS[0])
        hours = [self.game.start()[0]]
        for _ in self.ORDERS[0][1:]:
            messages = self.play_episode()
            hours.append(messages[1])
        self.assertEqual(hours, ["9 PM", "10 PM", "11 PM", "Near midnight", "Midnight"])

    def test_no_lure_can_be_had_before_its_critter_is_found(self):
        for species in self.ORDERS[0]:
            with self.subTest(species=species):
                self.setUp()
                self.game._order = [species]
                self.game.start()
                episode = self.game.episode
                if episode.unlock.blocked_exit is not None:
                    self.assertIsNone(_route(self.world, episode.lure_room))
                else:
                    self.go(episode.lure_room)
                    self.game.tapped()
                    self.assertIsNone(self.game.held)

    def test_the_critter_can_always_be_found_first(self):
        for species in self.ORDERS[0]:
            with self.subTest(species=species):
                self.setUp()
                self.game._order = [species]
                self.game.start()
                self.assertIsNotNone(_route(self.world, self.game.episode.hide_room))

    def test_each_found_critter_reveals_its_unlock(self):
        for species in self.ORDERS[0]:
            with self.subTest(species=species):
                self.setUp()
                self.game._order = [species]
                self.game.start()
                self.go(self.game.episode.hide_room)
                self.assertEqual(self.game.tapped()[-1], self.game.episode.unlock.reveal)

    def test_a_clue_pointing_at_the_critter_stops_once_it_is_found(self):
        self.game._order = ["dog"]
        self.game.start()
        self.assertEqual(self.go("Front Porch"), ["Woof! Tap the bottom edge"])
        self.go("Yard")
        self.game.tapped()
        self.assertEqual(self.go("Front Porch"), ["Tunnel! Tap the right edge"])

    def test_the_snowman_only_falls_once_the_reindeer_is_found(self):
        self.game._order = ["reindeer"]
        self.game.start()
        self.assertEqual(self.go("Yard"), ["He needs that nose"])
        self.go("Roof")
        self.game.tapped()
        self.assertEqual(self.go("Yard"), ["The snowman's flat!"])


class TestScene(HuntCase):
    """What each room shows, for scene_view to draw (cd-342.26)."""

    def test_an_empty_room_shows_nothing(self):
        self.walk(UP)
        scene = self.hunt.scene()
        self.assertEqual(
            (scene.spot, scene.critter, scene.lure, scene.follower, scene.held),
            (None, None, None, None, None),
        )

    def test_she_peeks_out_of_her_hiding_spot(self):
        self.walk(RIGHT, RIGHT, RIGHT)
        scene = self.hunt.scene()
        self.assertEqual(scene.spot, "potted plant")
        self.assertEqual(scene.critter, self.cat.sprite)
        self.assertEqual(scene.pose, hunt.HIDING)

    def test_once_found_she_waits_in_front_of_it(self):
        self.walk(RIGHT, RIGHT, RIGHT)
        self.hunt.tapped()
        self.assertEqual(self.hunt.scene().pose, hunt.WAITING)

    def test_the_lure_goes_into_your_hand(self):
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        scene = self.hunt.scene()
        self.assertIsNone(scene.lure)
        self.assertEqual(scene.held, "ball of yarn")

    def test_she_follows_you_home_and_leaves_her_spot(self):
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        self.walk(DOWN, RIGHT, RIGHT)
        self.hunt.tapped()
        scene = self.hunt.scene()
        self.assertIsNone(scene.critter)
        self.assertEqual(scene.spot, "potted plant")
        self.assertEqual(scene.follower, self.cat.sprite)
        self.assertIsNone(scene.held)
        self.walk(LEFT)
        self.assertEqual(self.hunt.scene().follower, self.cat.sprite)

    def test_the_batteries_are_always_in_the_odd_corner(self):
        self.walk(RIGHT, RIGHT, UP)
        self.assertEqual(self.hunt.scene().lure, "batteries")

    def test_the_end_shows_nothing(self):
        game = hunt.Hunt(rooms.make_world(), critters.make_roster(choice=first_choice), order=[])
        game.start()
        self.assertIsNone(game.scene().lure)


class TestLockedLures(unittest.TestCase):
    """A lure room that's open from the start shows what hides the lure."""

    def start(self, species):
        self.world = rooms.make_world()
        self.game = hunt.Hunt(
            self.world, critters.make_roster(choice=first_choice), order=[species])
        self.game.start()
        return episodes.EPISODES[species]

    def lure_while_locked_then_after(self, species):
        episode = self.start(species)
        self.world.current = episode.lure_room
        before = self.game.scene().lure
        self.world.current = episode.hide_room
        self.game.tapped()
        self.world.current = episode.lure_room
        return before, self.game.scene().lure

    def test_the_dark_garage_shows_nothing_until_the_lights_come_on(self):
        self.assertEqual(self.lure_while_locked_then_after("robot"), (None, "oil can"))

    def test_the_walnuts_are_in_plain_sight(self):
        self.assertEqual(self.lure_while_locked_then_after("squirrel"), ("walnuts", "walnuts"))

    def test_the_carrot_is_the_snowmans_nose_until_he_falls(self):
        self.assertEqual(self.lure_while_locked_then_after("reindeer"), ("snowman", "carrot"))


class TestEscapeAndBoxes(HuntCase):
    """The presents under the tree, and what the escape cutscene is told (cd-342.27/.10)."""

    def box(self, species):
        boxes = {b[0]: b[1:] for b in self.hunt.scene().boxes}
        return boxes[species]

    def test_the_start_is_an_escape_that_bolts_toward_the_hiding_place(self):
        self.assertEqual(self.hunt.event, hunt.ESCAPED)
        self.assertEqual(self.hunt.escape.species, "cat")
        self.assertEqual(self.hunt.escape.name, "Chirpy")
        self.assertEqual(self.hunt.escape.direction, RIGHT)  # to the Dining Room
        self.assertEqual(self.opening[self.hunt.escape_at], "Chirpy escaped!")

    def test_every_episode_bolts_along_its_first_step(self):
        for species, _lure, _habit, _sprites in critters.CAST:
            with self.subTest(species=species):
                world = rooms.make_world()
                game = hunt.Hunt(world, critters.make_roster(choice=first_choice), order=[species])
                game.start()
                path = episodes.spine(world, episodes.EPISODES[species])
                home = world.get(critters.HOME)
                self.assertEqual(home.exits[game.escape.direction], path[1])

    def test_only_the_tree_shows_boxes_one_per_critter_in_cast_order(self):
        boxes = self.hunt.scene().boxes
        self.assertEqual([b[0] for b in boxes], [c[0] for c in critters.CAST])
        self.walk(RIGHT)
        self.assertIsNone(self.hunt.scene().boxes)

    def test_her_box_is_empty_and_the_rest_are_shut(self):
        self.assertEqual(self.box("cat"), (hunt.BOX_EMPTY, self.cat.sprite))
        self.assertEqual(self.box("dog")[0], hunt.BOX_CLOSED)

    def test_her_box_stays_empty_until_she_is_back_then_she_sits_on_it(self):
        self.hunt._order = ["cat", "dog"]
        self.find_cat()
        self.walk(UP)
        self.hunt.tapped()
        self.walk(DOWN, RIGHT, RIGHT)
        self.hunt.tapped()  # she follows you
        self.walk(LEFT, LEFT)
        messages = self.walk(LEFT)
        self.assertEqual(self.box("cat")[0], hunt.BOX_HOME)
        self.assertEqual(self.box("dog")[0], hunt.BOX_EMPTY)
        self.assertEqual(self.hunt.event, hunt.ESCAPED)
        self.assertEqual(messages[0], "Chirpy curls up on the rug")
        self.assertEqual(messages[self.hunt.escape_at], self.hunt.critter.name + " escaped!")

    def test_moving_or_tapping_clears_the_escape_event(self):
        self.walk(RIGHT)
        self.assertIsNone(self.hunt.event)


class TestPlayerName(unittest.TestCase):
    def finished(self, player):
        game = hunt.Hunt(
            rooms.make_world(), critters.make_roster(choice=first_choice), order=[],
            player=player,
        )
        return game.start(), game

    def test_no_name_is_a_plain_merry_christmas(self):
        messages, _game = self.finished(None)
        self.assertEqual(messages, ["All home!", "Merry Christmas!"])

    def test_a_name_goes_in_its_own_caption(self):
        messages, game = self.finished("Sam")
        self.assertEqual(messages, ["All home!", "Merry Christmas,", "Sam!"])
        self.assertEqual(game.tapped(), ["Merry Christmas,", "Sam!"])


class TestWrap(unittest.TestCase):
    def test_short_text_stays_on_one_line(self):
        self.assertEqual(hunt.wrap("Nothing here"), ["Nothing here"])

    def test_wraps_on_word_boundaries(self):
        self.assertEqual(
            hunt.wrap("Chirpy loves fresh air!"), ["Chirpy loves", "fresh air!"]
        )

    def test_every_message_for_every_critter_fits_two_lines(self):
        templates = (
            "{name} escaped!", "{name} is home!",
            "{name} follows you home!", "{name} is with you. Go home!",
            "{name} wants the {short}", "Got the {item}!",
            "Batteries! Just out of reach",
            "All home! More critters soon", "Merry Christmas!", "So close!",
            "Nothing here", "{name} {habit}!", "{name} curls up on the rug",
            "All home!", "Merry Christmas,",
        ) + tuple(hunt._IMAGE_CLUE_TEXT.values()) + hunt._HOURS
        def episode_text(species):
            episode = episodes.EPISODES[species]
            unlock = episode.unlock
            texts = list(episode.closed_reasons.values())
            texts += [c.content for c in episode.clues if c.form == episodes.TEXT]
            texts += [unlock.reveal, unlock.blocked_text, unlock.locked_text, unlock.ready_text]
            return tuple(text for text in texts if text)

        for species, item, habit, sprites in critters.CAST:
            for _sprite, name in sprites:
                for template in templates + episode_text(species):
                    short = hunt._SHORT_ITEM.get(item, item)
                    text = template.format(name=name, item=item, habit=habit, short=short)
                    with self.subTest(text=text):
                        lines = hunt.wrap(text)
                        self.assertLessEqual(len(lines), 2, lines)
                        self.assertLessEqual(max(len(ln) for ln in lines), 15, lines)
                        for line in lines:
                            self.assertLessEqual(_px(line, _CAPTION), _CAPTION_PX, line)

    def test_the_wrap_widths_match_the_caption_font(self):
        self.assertEqual(len(hunt._CAPTION_WIDTHS), len(hunt._CAPTION_GLYPHS))
        for ch, width in zip(hunt._CAPTION_GLYPHS, hunt._CAPTION_WIDTHS):
            self.assertEqual(width, _CAPTION[ch], ch)
        self.assertEqual(hunt.text_px("Acorn wants the"), _px("Acorn wants the", _CAPTION))

    def test_wrap_breaks_a_line_that_is_short_but_too_wide(self):
        self.assertEqual(hunt.wrap("Acorn wants the walnuts"), ["Acorn wants", "the walnuts"])

    def test_every_room_name_fits_across_the_top(self):
        for room in rooms.make_world().all_rooms():
            with self.subTest(room=room.name):
                self.assertLessEqual(_px(room.name, _CAPTION), _ROOM_NAME_PX)


if __name__ == "__main__":
    unittest.main()

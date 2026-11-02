# SPDX-License-Identifier: MIT
# Off-device tests for game/hunt.py, played against the real map and episodes.
#
#   python3 Chapter_9/tests/test_hunt.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critters  # noqa: E402
import episodes  # noqa: E402
import hunt  # noqa: E402
import rooms  # noqa: E402
from rooms import DOWN, LEFT, RIGHT, UP  # noqa: E402


def first_choice(options):
    return options[0]


class HuntCase(unittest.TestCase):
    def setUp(self):
        self.world = rooms.make_world()
        self.roster = critters.make_roster(choice=first_choice)
        self.hunt = hunt.Hunt(self.world, self.roster)
        self.opening = self.hunt.start()
        self.cat = self.hunt.critter

    def walk(self, *directions):
        messages = []
        for direction in directions:
            self.assertTrue(self.world.move(direction), direction)
            messages = self.hunt.entered()
        return messages


class TestEscape(HuntCase):
    def test_first_episode_is_the_cat(self):
        self.assertEqual(self.hunt.episode.species, "cat")
        self.assertEqual(self.cat.state, critters.HIDING)
        self.assertEqual(self.cat.location, "Sun Porch")

    def test_opening_announces_the_escape_and_the_clue(self):
        self.assertEqual(self.opening, ["Chirpy escaped!", "Chirpy loves fresh air!"])

    def test_only_this_episodes_rooms_are_open(self):
        self.assertEqual(self.world.gate, set(self.hunt.episode.open_rooms))
        self.assertNotIn(LEFT, self.world.live_exits())

    def test_tapping_at_the_tree_repeats_the_clue(self):
        self.assertEqual(self.hunt.tapped(), ["Chirpy loves fresh air!"])


class TestFindingThings(HuntCase):
    def test_lure_room_says_to_tap(self):
        self.assertEqual(
            self.walk(RIGHT, UP), ["Ball of yarn here! Tap it."]
        )

    def test_tapping_the_lure_takes_it(self):
        self.walk(RIGHT, UP)
        self.assertEqual(self.hunt.tapped(), ["Got the ball of yarn!"])
        self.assertEqual(self.hunt.held, "ball of yarn")

    def test_lure_room_goes_quiet_once_taken(self):
        self.walk(RIGHT, UP)
        self.hunt.tapped()
        self.assertEqual(self.walk(DOWN, UP), [])
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_critter_without_the_lure_says_what_it_wants(self):
        self.assertEqual(
            self.walk(RIGHT, RIGHT, RIGHT), ["Something's here! Tap it."]
        )
        self.assertEqual(
            self.hunt.tapped(), ["Found Chirpy!", "She wants the ball of yarn"]
        )
        self.assertEqual(self.cat.state, critters.HIDING)

    def test_critters_without_a_chosen_pronoun_are_it(self):
        self.cat.name = critters.SPARE[0][1]
        self.walk(RIGHT, RIGHT, RIGHT)
        self.assertEqual(self.hunt.tapped()[1], "It wants the ball of yarn")

    def test_empty_room_tap(self):
        self.walk(UP)
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_odd_corner_shows_the_batteries_but_they_stay_out_of_reach(self):
        messages = self.walk(RIGHT, RIGHT, UP)
        self.assertIn("Batteries! Just out of reach", messages)
        self.assertEqual(self.hunt.tapped(), ["So close!"])
        self.assertIsNone(self.hunt.held)

    def test_yarn_clue_says_which_way_on_every_visit(self):
        self.assertEqual(self.walk(RIGHT), ["Yarn trail! Tap the top edge"])
        self.assertEqual(self.walk(LEFT, RIGHT), ["Yarn trail! Tap the top edge"])

    def test_tapping_a_clue_room_repeats_its_clue(self):
        self.walk(RIGHT)
        self.assertEqual(self.hunt.tapped(), ["Yarn trail! Tap the top edge"])

    def test_yarn_clue_stops_once_the_yarn_is_held(self):
        self.walk(RIGHT, UP)
        self.hunt.tapped()
        self.assertEqual(self.walk(DOWN), [])
        self.assertEqual(self.hunt.tapped(), ["Nothing here"])

    def test_breeze_clue_stays_after_taking_the_yarn(self):
        self.walk(RIGHT, UP)
        self.hunt.tapped()
        self.assertEqual(self.walk(DOWN, RIGHT), ["You feel a chilly breeze"])


class TestBumps(HuntCase):
    def test_closed_exit_gives_the_episodes_reason(self):
        self.assertEqual(self.hunt.bumped(LEFT), "brr! too cold out there")

    def test_no_exit_at_all_gives_no_reason(self):
        self.assertIsNone(self.hunt.bumped(DOWN))


class TestBringingItHome(HuntCase):
    def fetch(self):
        self.walk(RIGHT, UP)
        self.hunt.tapped()
        self.walk(DOWN, RIGHT, RIGHT)

    def test_tapping_with_the_lure_brings_it_along(self):
        self.fetch()
        self.assertEqual(self.hunt.tapped(), ["Chirpy follows you home!"])
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
        # Reuses the cat's episode under the dog, until cd-342.14 adds real ones.
        cat = episodes.EPISODES["cat"]
        dog = episodes.Episode(
            "dog", ("Living Room", "Hallway"), "Hallway", "Living Room", {}, ()
        )
        with_dog = dict(episodes.EPISODES, dog=dog)
        original = episodes.EPISODES
        episodes.EPISODES = with_dog
        self.addCleanup(setattr, episodes, "EPISODES", original)

        world = rooms.make_world()
        roster = critters.make_roster(choice=first_choice)
        game = hunt.Hunt(world, roster, order=["cat", "dog"])
        game.start()
        for direction in (RIGHT, UP):
            world.move(direction)
            game.entered()
        game.tapped()
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
            messages, ["Chirpy curls up on the rug", "Patch escaped!"]
        )
        self.assertEqual(game.episode, dog)
        self.assertEqual(world.gate, set(dog.open_rooms))
        self.assertEqual(game.stage, hunt.HUNTING)
        self.assertIsNot(cat, dog)

    def test_unwritten_episodes_are_skipped(self):
        world = rooms.make_world()
        roster = critters.make_roster(choice=first_choice)
        game = hunt.Hunt(world, roster)
        self.assertEqual(game.start()[0], "Chirpy escaped!")
        self.assertEqual(game._order, ["cat"])


class TestWrap(unittest.TestCase):
    def test_short_text_stays_on_one_line(self):
        self.assertEqual(hunt.wrap("Nothing here"), ["Nothing here"])

    def test_wraps_on_word_boundaries(self):
        self.assertEqual(
            hunt.wrap("Chirpy loves fresh air!"), ["Chirpy loves", "fresh air!"]
        )

    def test_every_message_for_every_critter_fits_two_lines(self):
        templates = (
            "{name} escaped!", "{name} is home!", "Found {name}!",
            "{name} follows you home!", "{name} is with you. Go home!",
            "It wants the {item}", "She wants the {item}", "Got the {item}!", "{item} here! Tap it.",
            "Something's here! Tap it.", "Batteries! Just out of reach",
            "All home! More critters soon", "Merry Christmas!", "So close!",
            "Nothing here", "{name} {habit}!", "{name} curls up on the rug",
        ) + tuple(hunt._IMAGE_CLUE_TEXT.values())
        reasons = tuple(
            reason
            for episode in episodes.EPISODES.values()
            for reason in episode.closed_reasons.values()
        )
        for _species, item, habit, sprites in critters.CAST:
            for _sprite, name in sprites:
                for template in templates + reasons:
                    text = template.format(name=name, item=item, habit=habit)
                    with self.subTest(text=text):
                        lines = hunt.wrap(text)
                        self.assertLessEqual(len(lines), 2, lines)
                        self.assertLessEqual(max(len(ln) for ln in lines), 15, lines)


if __name__ == "__main__":
    unittest.main()

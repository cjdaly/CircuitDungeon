# SPDX-License-Identifier: MIT
# Off-device tests for game/episodes.py -- every authored episode's shape is
# checked against the real map (rooms.make_world()) and cast (critters.CAST),
# per doc/EPISODES.md sec 2/7. Pure data, no hardware.
#
#   python3 Chapter_9/tests/test_episodes.py

import os
import random
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critters  # noqa: E402
import episodes  # noqa: E402
import rooms  # noqa: E402

# A caption is at most 2 Bangers lines of ~14 chars (doc/STYLE.md sec 3).
CAPTION_MAX = 28
SPECIES = [sp for sp, _lure, _habit, _sprites in critters.CAST]
LURE = {sp: lure for sp, lure, _habit, _sprites in critters.CAST}
NAMES = {sp: [name for _id, name in sprites] for sp, _lure, _habit, sprites in critters.CAST}


def _open_neighbours(world, episode, name):
    return [dest for dest in world.get(name).exits.values() if dest in episode.open_rooms]


def _side_branches(world, episode, path):
    """Open rooms off the path, grouped into branches: [(spine indexes, rooms)]."""
    on_path = set(path)
    seen = set()
    branches = []
    for name in sorted(episode.open_rooms - on_path):
        if name in seen:
            continue
        group, frontier, attach = {name}, [name], set()
        while frontier:
            for dest in _open_neighbours(world, episode, frontier.pop()):
                if dest in on_path:
                    attach.add(path.index(dest))
                elif dest not in group:
                    group.add(dest)
                    frontier.append(dest)
        seen |= group
        branches.append((attach, group))
    return branches


def _odd_corner_attach(moves):
    # The Odd Corner branches off room 3 -- or room 2 in a 3-move episode,
    # where room 3 is the critter's own room.
    return min(3, moves - 1)


class TestEveryEpisode(unittest.TestCase):
    """Shape rules from doc/EPISODES.md, applied to each authored episode."""

    def setUp(self):
        self.world = rooms.make_world()
        self.room_names = {room.name for room in self.world.all_rooms()}

    def _each(self):
        self.assertTrue(episodes.EPISODES)
        return sorted(episodes.EPISODES.items())

    def _shape(self, episode):
        path = episodes.spine(self.world, episode)
        self.assertIsNotNone(path, "hiding room unreachable")
        return path, _side_branches(self.world, episode, path)

    def test_keyed_by_a_cast_species(self):
        for species, episode in self._each():
            self.assertIn(species, SPECIES)
            self.assertEqual(episode.species, species)

    def test_open_rooms_exist_and_include_home_and_odd_corner(self):
        for _sp, episode in self._each():
            self.assertLessEqual(episode.open_rooms, self.room_names)
            self.assertIn(critters.HOME, episode.open_rooms)
            self.assertIn(episodes.ODD_CORNER, episode.open_rooms)

    def test_open_rooms_form_a_tree_from_home(self):
        # Connected, and no loops: edges == rooms - 1. So there's one way to
        # the critter and every side branch really dead-ends.
        for species, episode in self._each():
            path, branches = self._shape(episode)
            reached = set(path).union(*[group for _a, group in branches])
            self.assertEqual(reached, set(episode.open_rooms), species)
            edges = sum(len(_open_neighbours(self.world, episode, n)) for n in episode.open_rooms) // 2
            self.assertEqual(edges, len(episode.open_rooms) - 1, species)

    def test_path_length(self):
        # Chris: episode 1 is 3 moves; the rest 4, and at most one is 5.
        fives = 0
        for species, episode in self._each():
            moves = len(self._shape(episode)[0]) - 1
            if species == episodes.FIRST:
                self.assertEqual(moves, 3, species)
            else:
                self.assertIn(moves, (4, 5), species)
                fives += moves == 5
        self.assertLessEqual(fives, 1)

    def test_every_branch_hangs_off_one_spine_room(self):
        for species, episode in self._each():
            for attach, group in self._shape(episode)[1]:
                self.assertEqual(len(attach), 1, (species, group))

    def test_odd_corner_branch_leaves_the_path_at_room_3(self):
        for species, episode in self._each():
            path, branches = self._shape(episode)
            self.assertNotIn(episodes.ODD_CORNER, path)
            odd = [(a, g) for a, g in branches if episodes.ODD_CORNER in g][0]
            self.assertEqual(odd[0], {_odd_corner_attach(len(path) - 1)}, species)
            self.assertLessEqual(len(odd[1]), 2, species)
            self.assertEqual(len(_open_neighbours(self.world, episode, episodes.ODD_CORNER)), 1)

    def test_odd_corner_never_next_to_the_tree_on_the_whole_map(self):
        exits = self.world.get(critters.HOME).exits.values()
        self.assertNotIn(episodes.ODD_CORNER, exits)

    def test_rooms_before_the_odd_corner_branch_have_false_paths(self):
        # Rooms 1 and 2 (room 1 in episode 1) each get a dead-end side branch
        # of their own -- not the Odd Corner's.
        for species, episode in self._each():
            path, branches = self._shape(episode)
            plain = [a for a, g in branches if episodes.ODD_CORNER not in g]
            for index in range(1, _odd_corner_attach(len(path) - 1)):
                self.assertIn({index}, plain, (species, path[index]))

    def test_lure_is_in_a_side_branch_not_the_odd_corners(self):
        for species, episode in self._each():
            branches = self._shape(episode)[1]
            holding = [g for _a, g in branches if episode.lure_room in g]
            self.assertEqual(len(holding), 1, species)
            self.assertNotIn(episodes.ODD_CORNER, holding[0], species)

    def test_at_least_one_pure_false_path(self):
        # A side branch with neither the lure nor the Odd Corner in it.
        for species, episode in self._each():
            branches = self._shape(episode)[1]
            pure = [g for _a, g in branches
                    if episode.lure_room not in g and episodes.ODD_CORNER not in g]
            self.assertTrue(pure, species)

    def test_hide_and_lure_rooms_are_distinct_and_not_special(self):
        for _sp, episode in self._each():
            for name in (episode.hide_room, episode.lure_room):
                self.assertIn(name, episode.open_rooms)
                self.assertNotIn(name, (critters.HOME, episodes.ODD_CORNER))
            self.assertNotEqual(episode.hide_room, episode.lure_room)

    def test_every_closed_exit_has_a_reason_and_no_stale_reasons(self):
        for _sp, episode in self._each():
            expected = set()
            for name in episode.open_rooms:
                for direction, dest in self.world.get(name).exits.items():
                    if dest not in episode.open_rooms:
                        expected.add((name, direction))
            self.assertEqual(set(episode.closed_reasons), expected)

    def test_clues_are_well_formed_and_in_open_rooms(self):
        for _sp, episode in self._each():
            for clue in episode.clues:
                self.assertIn(clue.when, episodes.CLUE_WHENS)
                self.assertIn(clue.form, episodes.CLUE_FORMS)
                self.assertIn(clue.room, episode.open_rooms)
                if clue.when == episodes.ON_ESCAPE:
                    self.assertEqual(clue.room, critters.HOME)

    def test_has_an_escape_clue(self):
        for _sp, episode in self._each():
            self.assertTrue(episode.clues_for(episodes.ON_ESCAPE, critters.HOME))

    def test_text_fits_a_caption_for_every_name(self):
        for species, episode in self._each():
            texts = list(episode.closed_reasons.values())
            texts += [c.content for c in episode.clues if c.form == episodes.TEXT]
            for text in texts:
                for name in NAMES[species]:
                    self.assertLessEqual(len(text.format(name=name)), CAPTION_MAX, text)


class TestEpisodeOne(unittest.TestCase):
    """The cat -- what the gate actually does on the real map."""

    def setUp(self):
        self.world = rooms.make_world()
        self.cat = episodes.EPISODES["cat"]
        self.cat.open_on(self.world)

    def test_path_is_dining_kitchen_laundry(self):
        self.assertEqual(
            episodes.spine(self.world, self.cat),
            ["Living Room", "Dining Room", "Kitchen", "Laundry Room"],
        )

    def test_tree_shows_path_and_false_path_open_entryway_closed(self):
        self.assertEqual(self.world.live_exits(), [rooms.UP, rooms.RIGHT])
        self.assertEqual(self.world.closed_exits(), [rooms.LEFT])
        self.assertEqual(self.cat.reason_for("Living Room", rooms.LEFT), "brr! too cold out there")

    def test_kitchen_stairs_are_closed_with_a_reason(self):
        self.world.move(rooms.RIGHT)
        self.world.move(rooms.RIGHT)
        self.assertEqual(self.world.current, "Kitchen")
        self.assertEqual(self.world.closed_exits(), [rooms.DOWN])
        self.assertFalse(self.world.move(rooms.DOWN))
        self.assertEqual(self.cat.reason_for("Kitchen", rooms.DOWN), "too dark down there")

    def test_odd_corner_is_up_from_the_kitchen(self):
        self.world.move(rooms.RIGHT)
        self.world.move(rooms.RIGHT)
        self.assertTrue(self.world.move(rooms.UP))
        self.assertEqual(self.world.current, episodes.ODD_CORNER)
        self.assertEqual(self.world.live_exits(), [rooms.DOWN])

    def test_retrieval_loop_works_on_the_gated_map(self):
        critter = critters.make_roster(choice=lambda seq: seq[0]).get("Chirpy")
        critter.escape(self.cat.hide_room)
        held = set()
        for direction in (rooms.RIGHT, rooms.UP):  # Dining Room, Sewing Nook
            self.assertTrue(self.world.move(direction))
        if self.world.current == self.cat.lure_room:
            held.add(LURE["cat"])
        for direction in (rooms.DOWN, rooms.RIGHT, rooms.RIGHT):  # back, Kitchen, Laundry
            self.assertTrue(self.world.move(direction))
        self.assertTrue(critter.try_retrieve(self.world.current, held))

    def test_no_gate_after_finale_opens_everything(self):
        self.world.set_gate(None)
        self.world.move(rooms.RIGHT)
        self.world.move(rooms.RIGHT)
        self.assertTrue(self.world.move(rooms.DOWN))


class TestOrder(unittest.TestCase):
    def test_first_and_last_are_cast_species(self):
        self.assertIn(episodes.FIRST, SPECIES)
        self.assertIn(episodes.LAST, SPECIES)

    def test_bookends_fixed_middle_is_a_permutation(self):
        order = episodes.make_order(SPECIES, randrange=lambda n: 0)
        self.assertEqual(order[0], episodes.FIRST)
        self.assertEqual(order[-1], episodes.LAST)
        self.assertEqual(sorted(order), sorted(SPECIES))

    def test_middle_actually_shuffles(self):
        middles = {tuple(episodes.make_order(SPECIES, randrange=lambda n, k=k: k % n)[1:-1])
                   for k in range(6)}
        self.assertGreater(len(middles), 1)

    def test_default_is_random_and_seedable(self):
        random.seed(3)
        a = episodes.make_order(SPECIES)
        random.seed(3)
        self.assertEqual(episodes.make_order(SPECIES), a)


if __name__ == "__main__":
    unittest.main()

# SPDX-License-Identifier: MIT
# Off-device tests for game/walk.py -- pure logic, no hardware needed.
#
#   python3 Chapter_9/tests/test_walk.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

from rooms import DOWN, LEFT, RIGHT, UP  # noqa: E402
from walk import Patrol, bob, come_in  # noqa: E402


def run(patrol, seconds, tick=0.05, start=0.0):
    """All (t, x, y, moving, facing_right) samples over `seconds`."""
    out, t = [], start
    while t <= start + seconds + 1e-9:
        out.append((t,) + patrol.update(t))
        t += tick
    return out


class TestPatrol(unittest.TestCase):
    def test_needs_two_waypoints(self):
        with self.assertRaises(ValueError):
            Patrol([(0, 0)])

    def test_first_update_places_on_first_waypoint_not_moving(self):
        p = Patrol([(10, 20), (110, 20)])
        self.assertEqual(p.update(5.0), (10, 20, False, False))

    def test_moves_toward_next_waypoint_at_speed(self):
        p = Patrol([(0, 0), (100, 0)], speed=40.0)
        p.update(0.0)
        x, y, moving, _ = p.update(1.0)  # dt clamps to 0.25 -> 10px
        self.assertTrue(moving)
        self.assertEqual((x, y), (10, 0))

    def test_long_gap_is_clamped_not_teleported(self):
        p = Patrol([(0, 0), (1000, 0)], speed=40.0)
        p.update(0.0)
        x, _, _, _ = p.update(60.0)
        self.assertLessEqual(x, 10)

    def test_faces_right_when_heading_right_left_when_heading_left(self):
        p = Patrol([(0, 0), (60, 0)], speed=40.0, pause=0.2)
        samples = run(p, 6.0)
        moving = [s for s in samples if s[3]]
        self.assertTrue(moving[0][4])  # first leg heads right
        self.assertFalse(moving[-1][4])  # return leg heads left
        self.assertTrue(any(s[4] for s in moving) and any(not s[4] for s in moving))

    def test_facing_sticks_through_vertical_leg_and_pause(self):
        # right, then straight down, then left: while going down it must
        # keep facing right; it only flips when the leftward leg starts.
        p = Patrol([(0, 0), (60, 0), (60, 60), (0, 60)], speed=40.0, pause=0.3)
        samples = run(p, 9.0)
        down = [s for s in samples if s[3] and s[1] == 60 and 0 < s[2] < 60]
        self.assertTrue(down)
        self.assertTrue(all(s[4] for s in down))
        left = [s for s in samples if s[3] and s[2] == 60 and 0 < s[1] < 60]
        self.assertTrue(left)
        self.assertTrue(all(not s[4] for s in left))

    def test_pauses_at_each_waypoint(self):
        p = Patrol([(0, 0), (20, 0)], speed=40.0, pause=1.0)
        samples = run(p, 3.0)
        first_stop = next(i for i, s in enumerate(samples) if s[1] == 20 and not s[3])
        window = samples[first_stop:first_stop + 15]  # 0.75s later, still parked
        self.assertTrue(all(not s[3] and s[1] == 20 for s in window))

    def test_loops_forever_and_stays_on_the_path(self):
        wps = [(30, 96), (178, 96), (178, 140), (30, 140)]
        p = Patrol(wps, speed=40.0, pause=0.4)
        samples = run(p, 40.0)
        for _t, x, y, _m, _f in samples:
            self.assertTrue(30 <= x <= 178 and 96 <= y <= 140, (x, y))
        # visited every corner at least once (i.e. it really looped)
        corners = {(s[1], s[2]) for s in samples}
        for wp in wps:
            self.assertIn(wp, corners)


class TestBob(unittest.TestCase):
    def test_range_and_period(self):
        vals = [bob(t * 0.01, 0.2, 2) for t in range(0, 100)]
        self.assertEqual(min(vals), 0)
        self.assertEqual(max(vals), 2)
        self.assertEqual(bob(0.0, 0.2, 2), 0)  # on the ground at each step
        self.assertEqual(bob(0.1, 0.2, 2), 2)  # peak mid-step
        self.assertEqual(bob(0.2, 0.2, 2), 0)



class TestComeIn(unittest.TestCase):
    """cd-342.50: a follower walks in from the edge you came through."""

    HOME = (88, 104)

    def test_it_starts_just_off_its_edge(self):
        starts = {edge: come_in(edge, self.HOME, 0.0, 1.2)[:2]
                  for edge in (LEFT, RIGHT, UP, DOWN)}
        self.assertEqual(starts, {LEFT: (-64, 104), RIGHT: (240, 104),
                                  UP: (88, -64), DOWN: (88, 240)})

    def test_it_arrives_and_stops(self):
        for edge in (LEFT, RIGHT, UP, DOWN):
            self.assertEqual(come_in(edge, self.HOME, 1.2, 1.2), (88, 104, False))
            self.assertEqual(come_in(edge, self.HOME, 5.0, 1.2), (88, 104, False))
            self.assertTrue(come_in(edge, self.HOME, 0.6, 1.2)[2])

    def test_by_the_top_it_can_walk_forward_from_the_back(self):
        # cd-342.51: no dropping in from the sky.
        self.assertEqual(come_in(UP, self.HOME, 0.0, 1.2, back=40)[:2], (88, 40))
        self.assertEqual(come_in(LEFT, self.HOME, 0.0, 1.2, size=32, back=40)[:2], (-32, 104))

    def test_it_slows_as_it_arrives(self):
        xs = [come_in(LEFT, self.HOME, t / 10, 1.2)[0] for t in range(13)]
        steps = [b - a for a, b in zip(xs, xs[1:])]
        self.assertGreater(steps[0], steps[-1])
        self.assertTrue(all(step >= 0 for step in steps))

if __name__ == "__main__":
    unittest.main()

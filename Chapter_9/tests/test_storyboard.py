# SPDX-License-Identifier: MIT
# Off-device tests for game/storyboard.py: what the hunt reports, as comic beats
# -- cd-342.47.4.
#
#   python3 Chapter_9/tests/test_storyboard.py

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "game"))

import critters  # noqa: E402
import escape  # noqa: E402
import finale  # noqa: E402
import hunt  # noqa: E402
import rooms  # noqa: E402
import story  # noqa: E402
import storyboard  # noqa: E402
from story import News  # noqa: E402


def _captions(beats):
    return [beat.caption for beat in beats if beat.caption]


class TestCaptions(unittest.TestCase):
    def test_each_message_is_a_caption_in_order(self):
        beats = storyboard.beats(News(["Nothing here", "So close!"]))
        self.assertEqual(_captions(beats), ["Nothing here", "So close!"])
        self.assertTrue(all(beat.shot is None for beat in beats))

    def test_a_long_message_runs_on_two_lines_a_caption(self):
        beats = storyboard.beats(News(["one two three four five six seven eight"]))
        self.assertEqual(_captions(beats), ["one two three\nfour five six", "seven eight"])

    def test_no_messages_no_beats(self):
        self.assertEqual(storyboard.beats(News([])), [])

    def test_a_call_is_a_balloon_at_its_exit_after_the_captions(self):
        # cd-342.48: MEDIUM's critter, heard from the next room.
        beats = storyboard.beats(News(["So close!"], call=("Mew!", rooms.RIGHT)))
        self.assertEqual(_captions(beats), ["So close!"])
        self.assertEqual(beats[-1].speech, "Mew!")
        self.assertGreater(beats[-1].tail[0], 180)  # by the right edge
        alone = storyboard.beats(News([], call=("Woof!", rooms.UP)))
        self.assertEqual([b.speech for b in alone], ["Woof!"])
        self.assertLess(alone[0].tail[1], 60)


class TestEvents(unittest.TestCase):
    def test_finding_shouts_first_and_thinks_of_the_lure(self):
        beats = storyboard.beats(News(["Chirpy wants the yarn"], event=story.FOUND,
                                      want="ball of yarn"), icon=lambda name: ("icon", name))
        self.assertEqual(beats[0].burst, "Found!")
        self.assertEqual(beats[1].caption, "Chirpy wants\nthe yarn")
        self.assertEqual(beats[1].thought, ("icon", "ball of yarn"))

    def test_bringing_one_home_adds_hearts(self):
        beats = storyboard.beats(News(["Chirpy follows you home!"], event=story.RETRIEVED))
        self.assertTrue(beats[0].emanata)
        self.assertIsNone(beats[0].burst)

    def test_other_events_are_just_captions(self):
        beats = storyboard.beats(News(["Got the yarn!"], event=story.TOOK))
        self.assertEqual(len(beats), 1)
        self.assertFalse(beats[0].emanata or beats[0].burst or beats[0].thought)

    def test_a_bonk_is_a_shaking_burst(self):
        (beat,) = storyboard.bonk()
        self.assertEqual(beat.burst, "Bonk!")
        self.assertTrue(beat.shake)


class TestCutscenes(unittest.TestCase):
    def test_the_escape_plays_before_its_message_with_the_box_shut_till_then(self):
        news = News(["9 PM", "Chirpy escaped!", "A clue"],
                    cutscenes=((1, story.ESCAPE_SCENE),))
        beats = storyboard.beats(news)
        shots = [beat.shot for beat in beats]
        cut = len(escape.cutscene())
        self.assertEqual(shots, [escape.CALM] + [b.shot for b in escape.cutscene()] + [None, None])
        self.assertEqual(beats[0].caption, "9 PM")
        self.assertEqual(_captions(beats[1 + cut:]), ["Chirpy escaped!", "A clue"])

    def test_a_finale_cutscene_has_its_shots_before_and_after(self):
        news = News(["All home!", "Uh oh!"], cutscenes=((1, finale.BURST_SCENE),))
        beats = storyboard.beats(news)
        _make, before, after = finale.CUTSCENES[finale.BURST_SCENE]
        self.assertEqual(beats[0].shot, before)
        self.assertEqual(beats[-1].shot, after)
        self.assertEqual(len(beats), 2 + len(finale.burst()))

    def test_the_tower_is_as_tall_as_the_parade(self):
        for size in (2, 5, 7):
            news = News(["Up!", "Got them!"], cutscenes=((1, finale.TOWER_SCENE),), parade=size)
            towers = [b for b in storyboard.beats(news) if b.burst == "Hup!"]
            self.assertEqual(len(towers), min(size, finale.MAX_TOWER), size)


class TestFromTheHunt(unittest.TestCase):
    """Hunt.news() carries everything the storyboard needs."""

    def setUp(self):
        self.world = rooms.make_world()
        self.hunt = hunt.Hunt(self.world, critters.make_roster(choice=lambda o: o[0]),
                              order=["cat", "dog"])

    def test_the_opening_is_the_escape_about_the_critter_that_got_out(self):
        news = self.hunt.news(self.hunt.start())
        self.assertEqual(news.event, story.ESCAPED)
        self.assertEqual(news.escape.name, "Chirpy")
        beats = storyboard.beats(news)
        self.assertIn(escape.BOLT, [beat.shot for beat in beats])

    def test_the_escape_is_only_told_with_its_cutscene(self):
        self.hunt.start()
        self.world.move(rooms.RIGHT)
        news = self.hunt.news(self.hunt.entered())
        self.assertIsNone(news.escape)
        self.assertEqual(news.cutscenes, ())

    def test_the_parade_is_counted_for_the_tower(self):
        self.hunt.skip_to_finale()
        news = self.hunt.news(self.hunt.start())
        self.assertEqual(news.event, story.BURST)
        self.assertEqual(news.parade, len(critters.CAST))  # every critter bursts out


if __name__ == "__main__":
    unittest.main()

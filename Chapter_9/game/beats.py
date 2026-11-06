# SPDX-License-Identifier: MIT
"""Comic beats and the player that runs them in order -- cd-342.9.

A Beat is plain data saying what's on screen for a moment: a caption, a speech
balloon, a thought bubble, an SFX burst, some emanata, or several at once. Scenes
like the escape (cd-342.10) are then just lists of beats. BeatPlayer shows each
in turn; a beat ends when its time runs out or the player taps.

Drawing is the stage's job (comic.Stage), so this runs under plain desktop Python
(see tests/test_beats.py).
"""

_TEXT_BASE_S = 2.0  # how long words stay up: base + per character
_TEXT_PER_CHAR_S = 0.05
_BURST_S = 0.8
_PICTURE_S = 2.0


class Beat:
    def __init__(self, caption=None, speech=None, tail=None, thought=None, burst=None,
                 emanata=(), shake=False, duration=None, shot=None):
        """
        caption: text, a newline between its two lines at most
        speech, tail: balloon text, and the (x, y) its tail points at
        thought: the (bitmap, palette) of a 16x16 icon
        burst: one shouted word
        emanata: (glyph name, x, y) tuples, at most comic.MAX_EMANATA
        shake: jolt the scene under the overlay
        duration: seconds; None picks one from the content
        shot: what the scene under the words shows, for a cutscene (home_view)
        """
        self.caption = caption
        self.speech = speech
        self.tail = tail
        self.thought = thought
        self.burst = burst
        self.emanata = emanata
        self.shake = shake
        self.shot = shot
        self.duration = self._default_duration() if duration is None else duration

    def _default_duration(self):
        words = self.caption or self.speech
        if words:
            return _TEXT_BASE_S + _TEXT_PER_CHAR_S * len(words)
        return _BURST_S if self.burst else _PICTURE_S


class BeatPlayer:
    """Shows beats on a stage, which needs .show(beat, now) and .clear()."""

    def __init__(self, stage):
        self._stage = stage
        self._waiting = []
        self._ends_at = None

    @property
    def active(self):
        return self._ends_at is not None

    def play(self, beats, now):
        """Start `beats`, replacing whatever is playing. No beats clears the stage."""
        self._waiting = list(beats)
        self._next(now)

    def tap(self, now):
        """The player tapped: on to the next beat."""
        if self.active:
            self._next(now)

    def update(self, now):
        """Call once per frame."""
        if self.active and now >= self._ends_at:
            self._next(now)

    def _next(self, now):
        if self._waiting:
            beat = self._waiting.pop(0)
            self._stage.show(beat, now)
            self._ends_at = now + beat.duration
        else:
            self._stage.clear()
            self._ends_at = None

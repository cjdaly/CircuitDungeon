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
    """Shows beats on a stage, which needs .show(beat, now) and .clear().

    play() and tap() only say what should happen; update() does it, so the
    stage only ever draws from the loop's update pass (doc/ARCHITECTURE.md
    sec 1: drawing text is deep, so it happens at one known depth).
    """

    def __init__(self, stage):
        self._stage = stage
        self._waiting = []
        self._ends_at = None
        self._restart = False  # play() was called: start over at update()
        self._tapped = False  # tap() was called: on a beat at update()
        self.current = None  # the beat on screen

    @property
    def active(self):
        """A beat is up, or about to be (and not about to be cleared)."""
        if self._restart:
            return bool(self._waiting)
        return self._ends_at is not None

    def play(self, beats, now):
        """Queue `beats`, replacing whatever is playing; update() shows the
        first. No beats clears the stage."""
        self._waiting = list(beats)
        self._restart = True
        self._tapped = False

    def tap(self, now):
        """The player tapped: on to the next beat, at update()."""
        if self.active:
            self._tapped = True

    def update(self, now):
        """Call once per frame: the only place beats are drawn."""
        if self._restart:
            self._restart = self._tapped = False
            self._next(now)
        elif self._ends_at is not None and (self._tapped or now >= self._ends_at):
            self._tapped = False
            self._next(now)

    def _next(self, now):
        if self._waiting:
            beat = self._waiting.pop(0)
            self.current = beat
            self._stage.show(beat, now)
            self._ends_at = now + beat.duration
        else:
            self.current = None
            self._stage.clear()
            self._ends_at = None

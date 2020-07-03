# The MIT License (MIT)
#
# Copyright (c) 2020 Chris J Daly (github user cjdaly)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import time, board, digitalio
import displayio, terminalio
import neopixel
from gamepadshift import GamePadShift
from game import util

px=neopixel.NeoPixel(board.NEOPIXEL, 1)

def init():
  game={}
  DSP=board.DISPLAY ; game['DSP']=DSP
  game['face_right'] = True
  game['hero_base'] = 36
  #
  game['gamepad'] = GamePadShift(
    digitalio.DigitalInOut(board.BUTTON_CLOCK),
    digitalio.DigitalInOut(board.BUTTON_OUT),
    digitalio.DigitalInOut(board.BUTTON_LATCH)
    )
  #
  game['terrMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    game['terrMap'][c]=i ; i+=1
  #
  game['group']=displayio.Group(max_size=8)
  #
  util.init_tilegrid(game, "terrain","map", 10,8,16,16, 0,0)
  util.init_label(game, "label1", terminalio.FONT, 26, 0xFF00FF, 0, 0, "")
  util.init_tilegrid(game, "heroes","hero", 1,1,16,24, 32,68)
  #
  DSP.show(game['group'])
  #
  return game

def play():
  game = init()
  util.load_map(game, 'default')
  cycle=0
  while True:
    if game['face_right']:
        game['hero'][0,0]=game['hero_base'] + cycle
    else:
        game['hero'][0,0]=game['hero_base'] + 9 + cycle
    util.button_stuff(game)
    util.update_label(game, 'label1')
    px.fill((0,3,5))
    time.sleep(0.1)
    cycle += 1
    if cycle == 4:
        cycle=0


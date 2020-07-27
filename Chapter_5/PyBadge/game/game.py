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
  util.init_label(game, "label1", terminalio.FONT, 26, 0x0000FF, 0, 0, "")
  util.init_sprite(game, "heroes","hero", 1,1,16,24, 32,68)
  util.init_tilegrid(game, "explosions","exp", 1,1,32,32, -32,-32)
  #
  DSP.show(game['group'])
  #
  game['expName'] = 'exp1'
  game['exp1'] = [0,1,2,3,4,5,6,7,8,9,10,11,20,21,22,23,24,25,26,27,28,29,30,31]
  game['exp2'] = [ 1 , 2 , 3 ]
  #
  return game

def play():
  game = init()
  px.fill((0,3,5))
  util.load_map(game, 'home')
  cycle=0
  while True:
    if game['face_right']:
        game['hero'][0,0]=game['hero_base'] + (cycle % 4)
    else:
        game['hero'][0,0]=game['hero_base'] + 9 + (cycle % 4)
    #
    expName = game['expName']
    if expName in game:
        expArr = game[expName]
        game['exp'][0,0] = expArr[cycle % len(expArr)]
    #
    util.handle_buttons(game)
    util.update_label(game, 'label1')
    util.check_exps(game)
    util.check_exits(game)

    # time.sleep(0.1)
    cycle += 1
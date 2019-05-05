# The MIT License (MIT)
#
# Copyright (c) 2019 Chris J Daly (github user cjdaly)
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

import board, displayio, terminalio
from gamepadshift import GamePadShift
from digitalio import DigitalInOut
from adafruit_display_text import label

def load_tilegrid(filename, w=16,h=16,tw=16,th=16):
  f = open("/dad/stuff/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def TM(game,c):
  if c in game['terrMap']:
    return game['terrMap'][c]
  else:
    return 8 # red flag

def load_joke(game, joke_name):
  game['map_txt']=[]
  with open("/dad/jokes/" + joke_name + ".dad") as f:
    for line in f:
      if line.startswith("/"):
        game['map_txt'].append(line[1:11])
  if 'map_tg' in game:
    for y in range(6):
      for x in range(10):
        game['map_tg'][x,y]=TM(game, game['map_txt'][y][x])

def init():
  game={}
  game['gamepad']=GamePadShift(DigitalInOut(board.BUTTON_CLOCK),DigitalInOut(board.BUTTON_OUT),DigitalInOut(board.BUTTON_LATCH))
  #
  game['terrMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    game['terrMap'][c]=i ; i+=1
  #
  grp=displayio.Group(max_size=8)
  game['group']=grp
  #
  game['map_tg']=load_tilegrid("terrain", 10,6)
  load_joke(game, 'paper')
  grp.append(game['map_tg'])
  #
  board.DISPLAY.show(grp)
  return game
  
def play():
  game = init()
  gPad=game['gamepad'] ; DSP=board.DISPLAY ; gpVal=0 ; done=False
  while not done:
    # game logic
    #
    gPad.get_pressed() # discard extra clicks
    DSP.wait_for_frame()
    gpVal=gPad.get_pressed()
    if gpVal == 33:
      done=True



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

import time, neopixel, board, digitalio, displayio
from gamepadshift import GamePadShift

px=neopixel.NeoPixel(board.NEOPIXEL, 1)

pad = GamePadShift(
    digitalio.DigitalInOut(board.BUTTON_CLOCK),
    digitalio.DigitalInOut(board.BUTTON_OUT),
    digitalio.DigitalInOut(board.BUTTON_LATCH)
    )

def load_tilegrid(filename,w,h,tw,th):
  f = open("/tiles/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def init_tilegrid(game, filename,name, w,h,tw,th, x,y):
  tg=load_tilegrid(filename, w,h,tw,th)
  tg.x=x ; tg.y=y
  game['group'].append(tg)
  game[name]=tg

def TM(game,c):
  if c in game['terrMap']:
    return game['terrMap'][c]
  else:
    return 8 # red flag

def load_map(game, name):
    game['mapText']=[]
    with open("/maps/" + name + ".map") as f:
        for line in f:
            if line.startswith("/"):
                game['mapText'].append(line[1:11])
        # update tilegrid
        for y in range(8):
            for x in range(10):
                game['map'][x,y]=TM(game, game['mapText'][y][x])


def init():
  game={}
  DSP=board.DISPLAY ; game['DSP']=DSP
  game['face_right'] = True
  game['hero_base'] = 36
  #
  game['terrMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    game['terrMap'][c]=i ; i+=1
  #
  game['group']=displayio.Group(max_size=8)
  #
  init_tilegrid(game, "terrain","map", 10,8,16,16, 0,0)
  init_tilegrid(game, "heroes","hero", 1,1,16,24, 32,68)
  #
  DSP.show(game['group'])
  #
  return game

game = init()
load_map(game, 'default')

def button_stuff(game):
    buttons=pad.get_pressed()
    if buttons == 0:
        pass
    elif buttons == 1:
        load_map(game, 'default')
    elif buttons == 2:
        pass
    elif buttons == 4:
        pass
    elif buttons == 8:
        if game['hero_base'] == 0:
            game['hero_base'] = 18
        elif game['hero_base'] == 18:
            game['hero_base'] = 36
        else:
            game['hero_base'] = 0
    elif buttons == 16:
        game['hero'].x += 2
        game['face_right']=True
    elif buttons == 32:
        game['hero'].y += 2
    elif buttons == 64:
        game['hero'].y -= 2
    elif buttons == 128:
        game['face_right']=False
        game['hero'].x -= 2
    else:
        print("button: " + str(buttons))
        load_map(game, 'default')

cycle=0

while True:
    if game['face_right']:
        game['hero'][0,0]=game['hero_base'] + cycle
    else:
        game['hero'][0,0]=game['hero_base'] + 9 + cycle
    button_stuff(game)
    px.fill((0,3,5))
    time.sleep(0.1)
    cycle += 1
    if cycle == 4:
        cycle=0
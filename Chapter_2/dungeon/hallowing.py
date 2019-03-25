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


import board, neopixel, displayio, terminalio
# from adafruit_display_text import label

def load_mapbmp(filename):
  f = open("/game/maps/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter())
  return tg
  
def load_tilegrid(filename, w=16,h=16,tw=16,th=16):
  f = open("/game/art/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def TM(game,c):
  if c in game['terr']:
    return game['terr'][c]
  else:
    return 0  

def load_map(game, mapname):
  game['map_tx']=[]
  i=0
  with open("/game/maps/" + mapname + ".map") as f:
    for line in f:
      if line.startswith("?"):
        game['terr']={}
        j=0
        for c in line[1:17]:
          game['terr'][c]=j
          j+=1
      elif line.startswith("/"):
        game['map_tx'].append(line[1:17])
        i+=1
  if 'map_tg' in game:
    for y in range(16):
      for x in range(16):
        game['map_tg'][x,y]=TM(game, game['map_tx'][y][x])

def init():
  board.DISPLAY.auto_brightness = False
  board.DISPLAY.brightness = 0.33
  NP_0=neopixel.NeoPixel(board.NEOPIXEL,1,brightness=0.5)
  NP_0[0]=(11,0,22)
  game={}
  game['NeoPix']=NP_0
  gr=displayio.Group(max_size=8)
  game['group']=gr
  # map=load_tilegrid("terrain")
  # game['map_tg']=map
  map=load_mapbmp('map0')
  game['map_bmp']=map
  load_map(game, 'map0')
  gr.append(map)
  board.DISPLAY.show(gr)
  return game


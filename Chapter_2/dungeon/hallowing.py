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
from adafruit_display_text import label
  
def load_tilegrid(filename, w=16,h=16,tw=16,th=16):
  f = open("/dungeon/art/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def TM(game,c):
  if c in game['tMap']:
    return game['tMap'][c]
  else:
    return 14 # red flag

def load_map(game, mapname):
  game['map_txt']=[]
  with open("/dungeon/maps/" + mapname + ".map") as f:
    for line in f:
      if line.startswith("/"):
        game['map_txt'].append(line[1:9])
  if 'map_tg' in game:
    for y in range(6):
      for x in range(8):
        game['map_tg'][x,y]=TM(game, game['map_txt'][y][x])

def cycle_lights(game):
  board.DISPLAY.auto_brightness = False
  board.DISPLAY.brightness = game['disp_BL']
  game['NeoPix'].brightness=game['np_BR']
  game['NeoPix'][0]=game['np_RBG']

def init():
  NP_0=neopixel.NeoPixel(board.NEOPIXEL,1,brightness=0.5)
  game={'disp_BL':0.33, 'NeoPix':NP_0, 'np_BR'=0.5, 'np_RGB'=(0,11,22)}
  game['tMap']={} ; i=0
  for c in "(_)=$o-[#]HIJWRB<hijwGY>MNP& ,.mnp`":
    game['tMap'][c]=i ; i+=1
  #
  gr=displayio.Group(max_size=8)
  game['group']=gr
  txt=label.Label(terminalio.FONT, max_glyphs=21, color=0x00FFFF)
  txt.x=0 ; txt.y=120
  txt.text="Hello World!"
  gr.append(txt)
  #
  game['map_tg']=load_tilegrid("terrain", 8,6)
  load_map(game, 'map0')
  gr.append(map)
  board.DISPLAY.show(gr)
  cycle_lights(game)
  return game


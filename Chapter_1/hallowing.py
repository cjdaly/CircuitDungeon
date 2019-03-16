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
from adafruit_display_text import text_area

def init():
  NP_0 = neopixel.NeoPixel(board.NEOPIXEL,1,brightness=0.5)
  NP_0[0]=(11,0,22)
  board.DISPLAY.auto_brightness = False
  board.DISPLAY.brightness = 0.33
  splash = displayio.Group(max_size=8)
  board.DISPLAY.show(splash)
  return splash

def title_text(title="Circuit\n Dungeon!"):
  ta = text_area.TextArea(terminalio.FONT, text=title)
  ta.scale=2
  ta.x=16
  ta.y=0
  return ta

def load_hero(filename, x=0, y=0):
  f = open("/tiles/heroes" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), position=(0,0), tile_width=16,tile_height=24)
  tg.position=(x,y)
  return tg

def load_map(mapname, x=0, y=0):
  f = open("/maps/" + mapname + "/" + mapname + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), position=(0,0))
  tg.position=(x,y)
  return tg

def test():
  splash = init()
  #title=title_text()
  #splash.append(title)
  #
  map=load_map("map1", -64,-48)
  splash.append(map)
  #
  pc=load_hero("knight_f",16,64)
  splash.append(pc)
  #
  return pc



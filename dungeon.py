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


import board, displayio

def init():
  board.DISPLAY.auto_brightness = False
  board.DISPLAY.brightness = 0.33
  splash = displayio.Group()
  board.DISPLAY.show(splash)
  return splash

def test():
  splash = init()
  title="Circuit\nDungeon"
  ta = text_area.TextArea(terminalio.FONT, text=title, scale=2)
  ta.x=4
  ta.y=4
  splash.append(ta)
  f = open("/tileset1/gateway.bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), position=(0,0))
  tg.position=(32,48)
  splash.append(tg)


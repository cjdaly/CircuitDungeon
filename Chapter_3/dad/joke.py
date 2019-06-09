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
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label

from dad import chomp_code

def load_tilegrid(filename,w,h,tw,th):
  f = open("/dad/stuff/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def init_tilegrid(game, filename,name, w,h,tw,th, x,y):
  tg=load_tilegrid(filename, w,h,tw,th)
  tg.x=x ; tg.y=y
  game['group'].append(tg)
  game[name]=tg

def init_label(game, name, font, len, color, x,y, text):
  lbl=label.Label(font, max_glyphs=len, color=color)
  lbl.x=x ; lbl.y=y; lbl.text=text
  game['group'].append(lbl)
  game[name]=lbl

def init():
  game={}
  game['gamepad']=GamePadShift(DigitalInOut(board.BUTTON_CLOCK),DigitalInOut(board.BUTTON_OUT),DigitalInOut(board.BUTTON_LATCH))
  DSP=board.DISPLAY ; game['DSP']=DSP
  #
  game['terrMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    game['terrMap'][c]=i ; i+=1
  #
  game['group']=displayio.Group(max_size=8)
  #
  init_tilegrid(game, "terrain","jokeRoom", 10,6,16,16, 0,16)
  #
  init_label(game, "textT", terminalio.FONT, 26, 0xFF00FF, 1, -33, "")
  init_label(game, "textB", terminalio.FONT, 26, 0x00FFFF, 1, -33, "")
  #
  init_tilegrid(game, "rugrats","rugrat1", 1,1,16,24, 32,68)
  init_tilegrid(game, "pets","pet1", 1,1,32,32, -33,-33)
  init_tilegrid(game, "snacks","snack1", 1,1,32,32, -33,-33)
  init_tilegrid(game, "sillies","silly1", 1,1,32,32, -33,-33)
  #
  font = bitmap_font.load_font("/dad/fonts/Helvetica-Bold-16.bdf")
  init_label(game, "textM", font, 18, 0xFFFF00, 8, -33, "")
  #
  DSP.show(game['group']) ; DSP.wait_for_frame()
  #
  return game

def play(game=None):
  DSP = board.DISPLAY
  if not game:
    game = init()
  CCPU = chomp_code.init(game)
  #
  gPad=game['gamepad']
  nomKey=['Noms','nOms','NoMs','noMs']
  pL=[-1,0,0,0] # frame, turn, level, gamepad
  pD={'spriteBase':0, 'faceRight':True}
  done=False
  #
  chomp_code.load_joke(game, CCPU, 'home')
  chomp_code.eval_noms('SUPs', game, CCPU, pL, pD)
  #
  while not done:
    pL[0]+=1
    if pL[0]>3:
      pL[0]=0 ; pL[1]+=1
    chomp_code.eval_noms(nomKey[pL[0]], game, CCPU, pL, pD)
    chomp_code.eval_noms('noms', game, CCPU, pL, pD)
    DSP.wait_for_frame()
    pL[3]=gPad.get_pressed()
    chomp_code.eval_noms('NOMs', game, CCPU, pL, pD)
    if pL[3] == 33:
      done=True
  return game


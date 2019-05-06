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

def load_tilegrid(filename,w,h,tw,th):
  f = open("/dad/stuff/" + filename + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def TM(game,c):
  if c in game['terrMap']:
    return game['terrMap'][c]
  else:
    return 8 # red flag

def WAIT_FRAME():
  board.DISPLAY.wait_for_frame()

def load_joke(game):
  game['jokeRoomTxt']=[]
  with open("/dad/jokes/" + game['joke'] + ".dad") as f:
    for line in f:
      if line.startswith("/"):
        game['jokeRoomTxt'].append(line[1:11])
      elif line.startswith(":T:"):
        game['textT'].text=line[3:].rstrip() ; WAIT_FRAME()
      elif line.startswith(":M:"):
        game['textM'].text=line[3:].rstrip() ; WAIT_FRAME()
      elif line.startswith(":B:"):
        game['textB'].text=line[3:].rstrip() ; WAIT_FRAME()
  for y in range(6):
    for x in range(10):
      game['jokeRoom'][x,y]=TM(game, game['jokeRoomTxt'][y][x])

def init_tilegrid(game, filename,name, w=1,h=1,tw=32,th=32, x,y):
  tg=load_tilegrid(filename, w,h,tw,th)
  tg.x=x ; rugrat1.y=y
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
  #
  game['joke']='home'
  game['terrMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    game['terrMap'][c]=i ; i+=1
  #
  game['group']=displayio.Group(max_size=8)
  #
  init_tilegrid(game, "terrain","jokeRoom", 10,6,16,16, 0,16)
  #
  init_label(game, "textT", terminalio.FONT, 26, 0xFF00FF, 1, 7, "Hello World! Hello World!A")
  init_label(game, "textB", terminalio.FONT, 26, 0x00FFFF, 1, 7, "Nullo World! Nullo World!Z")
  #
  init_tilegrid(game, "rugrats","rugrat1", 1,1,16,24, 32,68)
  init_tilegrid(game, "pets","pet1", 1,1,32,32, -33,-33)
  init_tilegrid(game, "snacks","snack1", 1,1,32,32, 96,60)
  init_tilegrid(game, "sillies","silly1", 1,1,32,32, -33,-33)
  #
  font = bitmap_font.load_font("/dad/fonts/Helvetica-Bold-16.bdf")
  init_label(game, "textM", font, 18, 0xFFFF00, 8, 58, "Mello Yello World!")
  #
  board.DISPLAY.show(game['group']) ; WAIT_FRAME()
  load_joke(game) ; WAIT_FRAME()
  #
  return game

def play():
  game = init()
  gPad=game['gamepad'] ; DSP=board.DISPLAY
  gpVal=0 ; iFr=0 ; iTr=0; done=False
  while not done:
    if iFr>3:
      iFr=0 ; iTr+=1
    game['rugrat1'][0,0]=iFr
    #
    gPad.get_pressed() # discard extra clicks
    WAIT_FRAME(); iFr=iFr+1
    DSP.auto_brightness = False ; DSP.brightness=0.5
    gpVal=gPad.get_pressed()
    if gpVal == 33:
      done=True
  return game


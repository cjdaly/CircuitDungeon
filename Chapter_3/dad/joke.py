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
  game['jokeRoomTxt']=[]
  with open("/dad/jokes/" + joke_name + ".dad") as f:
    for line in f:
      if line.startswith("/"):
        game['jokeRoomTxt'].append(line[1:11])
  if 'jokeRoom' in game:
    for y in range(6):
      for x in range(10):
        game['jokeRoom'][x,y]=TM(game, game['jokeRoomTxt'][y][x])

def init():
  game={}
  game['gamepad']=GamePadShift(DigitalInOut(board.BUTTON_CLOCK),DigitalInOut(board.BUTTON_OUT),DigitalInOut(board.BUTTON_LATCH))
  #
  game['joke']='home'
  game['terrMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    game['terrMap'][c]=i ; i+=1
  #
  grp=displayio.Group(max_size=8)
  game['group']=grp
  #
  jokeRoom=load_tilegrid("terrain", 10,6)
  game['jokeRoom']=jokeRoom
  jokeRoom.x=0 ; jokeRoom.y=16
  load_joke(game, game['joke'])
  grp.append(jokeRoom)
  #
  textT=label.Label(terminalio.FONT, max_glyphs=26, color=0xFF00FF)
  textT.x=1 ; textT.y=7
  textT.text="Hello World! Hello World!A"
  grp.append(textT)
  game['textT']=textT
  #
  textB=label.Label(terminalio.FONT, max_glyphs=26, color=0x00FFFF)
  textB.x=1 ; textB.y=119
  textB.text="Nullo World! Nullo World!Z"
  grp.append(textB)
  game['textB']=textB
  #
  rugrat1=load_tilegrid("rugrats", 1,1,16,24)
  rugrat1.x=32 ; rugrat1.y=68
  grp.append(rugrat1)
  game['rugrat1']=rugrat1
  #
  pet1=load_tilegrid("pets", 1,1,32,32)
  pet1.x=-33 ; pet1.y=-33
  grp.append(pet1)
  game['pet1']=pet1
  #
  snack1=load_tilegrid("snacks", 1,1,32,32)
  snack1.x=96 ; snack1.y=60
  grp.append(snack1)
  game['snack1']=snack1
  #
  silly1=load_tilegrid("sillies", 1,1,32,32)
  silly1.x=-33 ; silly1.y=-33
  grp.append(silly1)
  game['silly1']=silly1
  #
  font = bitmap_font.load_font("/dad/fonts/Helvetica-Bold-16.bdf")
  textM = label.Label(font, max_glyphs=18, color=0xFFFF00)
  textM.x=8 ; textM.y=60
  textM.text="Mello Yello World!"
  grp.append(textM)
  game['textM']=textM
  #
  board.DISPLAY.show(grp)
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
    DSP.wait_for_frame(); iFr=iFr+1
    DSP.auto_brightness = False ; DSP.brightness=0.5
    gpVal=gPad.get_pressed()
    if gpVal == 33:
      done=True
  return game


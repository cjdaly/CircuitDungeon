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


import terminalio, displayio, board
from adafruit_clue import clue
from game import util

def play():
  game={}
  DSP=board.DISPLAY ; game['DSP']=DSP
  game['group']=displayio.Group(max_size=8)
  #
  M = util.init_tilegrid(game, "ClueWorld","map", 1,1,500,500, 0,0)
  #
  textA = util.init_label(game, "textA", terminalio.FONT, 20, 0xFF80FF, 1, 200, "A")
  textB = util.init_label(game, "textB", terminalio.FONT, 20, 0xFF80FF, 200, 200, "B")
  textT = util.init_label(game, "textT", terminalio.FONT, 40, 0xFFFFFF, 1, 1, "Hello!!!")
  #
  DSP.show(game['group'])
  #
  updateT = False
  while True:
    if clue.button_a:
      M.x -= 10 ; updateT = True
    elif clue.button_b:
      M.x += 10 ; updateT = True
    elif clue.touch_0:
      M.y -= 10 ; updateT = True
    elif clue.touch_1:
      pass
    elif clue.touch_2:
      M.y += 10 ; updateT = True
    #
    if updateT:
      textT.text = "x: " + str(M.x) + ", y: " + str(M.y)
      upateT = False


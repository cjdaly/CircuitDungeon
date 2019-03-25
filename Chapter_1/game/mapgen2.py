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

import os

# #%_o><"RGBYx[X]
terrain = {
  ' ':"+0+0",
  '#':"+16+0",
  '%':"+32+0",
  '_':"+48+0",
  'o':"+0+16",
  '>':"+16+16",
  '<':"+32+16",
  '"':"+48+16",
  'R':"+0+32",
  'G':"+16+32",
  'B':"+32+32",
  'Y':"+48+32",
  'x':"+0+48",
  '[':"+16+48",
  'X':"+32+48",
  ']':"+48+48"
}

maps = ['map0', 'map1']

def generate_map(mapname):
  game={}
  game['map_tx']=[]
  i=0
  with open("maps/" + mapname + ".map") as f:
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
  for y in range(16):
    args=mapname + " " + str(y)
    for x in range(16):
      c=game['map_tx'][y][x]
      args+=" " + terrain[c]
    os.system("./draw-map-row2.sh " + args)


for map in maps:
  print(map)
  generate_map(map)



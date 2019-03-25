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

terrain = {
  '(':"+0+0",
  '_':"+16+0",
  ')':"+32+0",
  '[':"+0+16",
  '#':"+16+16",
  ']':"+32+16",
  'R':"+0+32",
  'B':"+16+32",
  '<':"+32+32",
  'G':"+0+48",
  'Y':"+16+48",
  '>':"+32+48",
  ' ':"+0+64",
  ',':"+16+64",
  '.':"+32+64",
  '-':"+48+0",
  'H':"+48+16",
  'h':"+48+32",
  'M':"+48+48",
  'm':"+48+64",
  '~':"+96+0",
  'W':"+96+16",
  'w':"+96+32",
  '&':"+96+48",
  '`':"+96+64",
  '=':"+48+0",
  '$':"+64+0",
  'o':"+80+0"
}

maps = ['map0', 'map1', 'map2']

def generate_map(mapname):
  map_txt=[]
  i=0
  with open("../dungeon/maps/" + mapname + ".map") as f:
    for line in f:
      if line.startswith("/"):
        map_txt.append(line[1:9])
        i+=1
  for y in range(6):
    args=mapname + " " + str(y)
    for x in range(8):
      c=map_txt[y][x]
      args+=" " + terrain[c]
    os.system("./draw-map-row.sh " + args)

for map in maps:
  print(map)
  generate_map(map)


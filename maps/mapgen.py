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

row=0
terrain = { }

def T(c):
  t=terrain[c]
  if ":" in t:
    return t.split(':')[0]
  else:
    return t

with open("map1/map1.map") as f:
  for line in f:
    if line.startswith("="):
      c=line[1]
      terrain[c]=line[3:].strip()
    elif line.startswith("/"):
      l=line[1:].strip()
      terr_args=""
      for i in range(16):
        terr_args+=" " + T(l[i])
      os.system("./draw-map-row.sh " + str(row) + terr_args)
      row+=1
    else:
      pass



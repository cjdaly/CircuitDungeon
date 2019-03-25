#!/bin/bash

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

tile16=16

map_name=$1
row=$2

MAP_bmp=maps/${map_name}.bmp
TERR_bmp=art/terrain.bmp

if [ "$row" == "0" ]; then
  rm -f $MAP_bmp
  convert -size 256x256 xc:transparent $MAP_bmp
fi

convert $MAP_bmp\
 \( $TERR_bmp -crop "16x16${3}" \) -geometry +$[tile16*0]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${4}" \) -geometry +$[tile16*1]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${5}" \) -geometry +$[tile16*2]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${6}" \) -geometry +$[tile16*3]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${7}" \) -geometry +$[tile16*4]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${8}" \) -geometry +$[tile16*5]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${9}" \) -geometry +$[tile16*6]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${10}" \) -geometry +$[tile16*7]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${11}" \) -geometry +$[tile16*8]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${12}" \) -geometry +$[tile16*9]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${13}" \) -geometry +$[tile16*10]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${14}" \) -geometry +$[tile16*11]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${15}" \) -geometry +$[tile16*12]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${16}" \) -geometry +$[tile16*13]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${17}" \) -geometry +$[tile16*14]+$[row*16] -composite\
 \( $TERR_bmp -crop "16x16${18}" \) -geometry +$[tile16*15]+$[row*16] -composite\
 $MAP_bmp


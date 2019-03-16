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
arg1=$1
row=$[arg1*16]

TS_dir=../ExtractedTilesets/tileset1
MAP_name=map1
MAP_bmp=$MAP_name/$MAP_name.bmp

if [ "$arg1" == "0" ]; then
  rm -f $MAP_bmp
  convert -size 256x256 xc:transparent $MAP_bmp
fi

convert $MAP_bmp\
 \( $TS_dir/${2-floor1}.bmp \) -geometry +$[tile16*0]+$row -composite\
 \( $TS_dir/${3-floor1}.bmp \) -geometry +$[tile16*1]+$row -composite\
 \( $TS_dir/${4-floor1}.bmp \) -geometry +$[tile16*2]+$row -composite\
 \( $TS_dir/${5-floor1}.bmp \) -geometry +$[tile16*3]+$row -composite\
 \( $TS_dir/${6-floor1}.bmp \) -geometry +$[tile16*4]+$row -composite\
 \( $TS_dir/${7-floor1}.bmp \) -geometry +$[tile16*5]+$row -composite\
 \( $TS_dir/${8-floor1}.bmp \) -geometry +$[tile16*6]+$row -composite\
 \( $TS_dir/${9-floor1}.bmp \) -geometry +$[tile16*7]+$row -composite\
 \( $TS_dir/${10-floor1}.bmp \) -geometry +$[tile16*8]+$row -composite\
 \( $TS_dir/${11-floor1}.bmp \) -geometry +$[tile16*9]+$row -composite\
 \( $TS_dir/${12-floor1}.bmp \) -geometry +$[tile16*10]+$row -composite\
 \( $TS_dir/${13-floor1}.bmp \) -geometry +$[tile16*11]+$row -composite\
 \( $TS_dir/${14-floor1}.bmp \) -geometry +$[tile16*12]+$row -composite\
 \( $TS_dir/${15-floor1}.bmp \) -geometry +$[tile16*13]+$row -composite\
 \( $TS_dir/${16-floor1}.bmp \) -geometry +$[tile16*14]+$row -composite\
 \( $TS_dir/${17-floor1}.bmp \) -geometry +$[tile16*15]+$row -composite\
 $MAP_bmp


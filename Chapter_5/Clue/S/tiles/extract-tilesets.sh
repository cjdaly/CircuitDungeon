#!/bin/bash

# The MIT License (MIT)
#
# Copyright (c) 2020 Chris J Daly (github user cjdaly), S. E. Daly
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

tile32=32
ART_src=../../../../sourceArt
ART_dst=tileset1

DC_png=$ART_src/DungeonCrawl/ProjectUtumno_full.png

rm -rf $ART_dst
mkdir $ART_dst

SLY_bmp=$ART_dst/sillies.bmp
convert -size 256x64 xc:black $SLY_bmp
convert $SLY_bmp\
 \( $DC_png -crop "32x32+$[tile32*47]+$[tile32*0]" \) -geometry +$[tile32*0]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*48]+$[tile32*0]" \) -geometry +$[tile32*1]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*49]+$[tile32*0]" \) -geometry +$[tile32*2]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*50]+$[tile32*0]" \) -geometry +$[tile32*3]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*51]+$[tile32*0]" \) -geometry +$[tile32*4]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*52]+$[tile32*0]" \) -geometry +$[tile32*5]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*53]+$[tile32*0]" \) -geometry +$[tile32*6]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*54]+$[tile32*0]" \) -geometry +$[tile32*7]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*63]+$[tile32*0]" \) -geometry +$[tile32*0]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*0]+$[tile32*1]" \) -geometry +$[tile32*1]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*1]+$[tile32*1]" \) -geometry +$[tile32*2]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*2]+$[tile32*1]" \) -geometry +$[tile32*3]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*3]+$[tile32*1]" \) -geometry +$[tile32*4]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*4]+$[tile32*1]" \) -geometry +$[tile32*5]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*5]+$[tile32*1]" \) -geometry +$[tile32*6]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*1]" \) -geometry +$[tile32*7]+$[tile32*1] -composite\
 $SLY_bmp

EXP_bmp=$ART_dst/explosions.bmp
convert -size 256x128 xc:black $EXP_bmp
convert $EXP_bmp\
 \( $DC_png -crop "32x32+$[tile32*38]+$[tile32*23]" \) -geometry +$[tile32*0]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*39]+$[tile32*23]" \) -geometry +$[tile32*1]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*40]+$[tile32*23]" \) -geometry +$[tile32*2]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*41]+$[tile32*23]" \) -geometry +$[tile32*3]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*4]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*5]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*6]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*7]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*0]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*1]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*2]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*3]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*4]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*5]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*6]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*7]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*0]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*1]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*2]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*3]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*4]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*5]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*6]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*7]+$[tile32*2] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*0]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*1]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*2]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*3]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*4]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*5]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*6]+$[tile32*3] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*0]" \) -geometry +$[tile32*7]+$[tile32*3] -composite\
 $EXP_bmp

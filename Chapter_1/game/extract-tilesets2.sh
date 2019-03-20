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
tile24=24
tile32=32
SRC_art=../../sourceArt
DT_png=$SRC_art/DungeonTileset/0x72_16x16DungeonTileset.v4.png
DT2_png=$SRC_art/DungeonTilesetII/0x72_DungeonTilesetII_v1.2.png
IND_png=$SRC_art/Industrial/industrial.v2.png

rm -rf art
mkdir art


TR_bmp=art/terrain.bmp
convert -size 64x64 xc:transparent $TR_bmp
convert $TR_bmp\
 \( $DT_png -crop "16x16+$[tile16*1]+$[tile16*1]" \) -geometry +$[tile16*0]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*2]+$[tile16*3]" \) -geometry +$[tile16*1]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*4]+$[tile16*7]" \) -geometry +$[tile16*2]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*4]+$[tile16*6]" \) -geometry +$[tile16*3]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*4]+$[tile16*0]" \) -geometry +$[tile16*0]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*4]+$[tile16*2]" \) -geometry +$[tile16*1]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*4]+$[tile16*3]" \) -geometry +$[tile16*2]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*7]+$[tile16*0]" \) -geometry +$[tile16*3]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*12]+$[tile16*4]" \) -geometry +$[tile16*0]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*13]+$[tile16*4]" \) -geometry +$[tile16*1]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*14]+$[tile16*4]" \) -geometry +$[tile16*2]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*15]+$[tile16*4]" \) -geometry +$[tile16*3]+$[tile16*2] -composite\
 \( $IND_png -crop "16x16+$[tile16*5]+$[tile16*0]" \) -geometry +$[tile16*0]+$[tile16*3] -composite\
 \( $IND_png -crop "16x16+$[tile16*12]+$[tile16*0]" \) -geometry +$[tile16*1]+$[tile16*3] -composite\
 \( $IND_png -crop "16x16+$[tile16*13]+$[tile16*0]" \) -geometry +$[tile16*2]+$[tile16*3] -composite\
 \( $IND_png -crop "16x16+$[tile16*15]+$[tile16*0]" \) -geometry +$[tile16*3]+$[tile16*3] -composite\
 $TR_bmp
 

OB_bmp=art/objects.bmp
convert -size 64x32 xc:transparent $OB_bmp
convert $OB_bmp\
 \( $DT2_png -crop "64x16+$[tile16*18]+$[tile16*14]" \) -geometry +$[tile16*0]+$[tile16*0] -composite\
 \( $DT2_png -crop "64x16+$[tile16*18]+$[tile16*15]" \) -geometry +$[tile16*0]+$[tile16*1] -composite\
 $OB_bmp


HR_bmp=art/heroes.bmp
convert -size 128x72 xc:transparent $HR_bmp
convert $HR_bmp\
 \( $DT2_png -crop "64x24+$[tile16*8]+$[tile16*2+8]" \) -geometry +$[tile16*0]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*8]+$[tile16*2+8]" -flop \) -geometry +$[tile16*4]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*9]+$[tile16*2+8]" -flop \) -geometry +$[tile16*5]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*10]+$[tile16*2+8]" -flop \) -geometry +$[tile16*6]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*11]+$[tile16*2+8]" -flop \) -geometry +$[tile16*7]+$[tile24*0] -composite\
 \( $DT2_png -crop "64x24+$[tile16*8]+$[tile16*4+8]" \) -geometry +$[tile16*0]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*8]+$[tile16*4+8]" -flop \) -geometry +$[tile16*4]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*9]+$[tile16*4+8]" -flop \) -geometry +$[tile16*5]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*10]+$[tile16*4+8]" -flop \) -geometry +$[tile16*6]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*11]+$[tile16*4+8]" -flop \) -geometry +$[tile16*7]+$[tile24*1] -composite\
 \( $DT2_png -crop "64x24+$[tile16*8]+$[tile16*8+8]" \) -geometry +$[tile16*0]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*8]+$[tile16*8+8]" -flop \) -geometry +$[tile16*4]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*9]+$[tile16*8+8]" -flop \) -geometry +$[tile16*5]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*10]+$[tile16*8+8]" -flop \) -geometry +$[tile16*6]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*11]+$[tile16*8+8]" -flop \) -geometry +$[tile16*7]+$[tile24*2] -composite\
 $HR_bmp


CR_bmp=art/creatures.bmp
convert -size 128x72 xc:transparent $CR_bmp
convert $CR_bmp\
 \( $DT2_png -crop "64x24+$[tile16*23]+$[tile16*4+8]" \) -geometry +$[tile16*0]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*23]+$[tile16*4+8]" -flop \) -geometry +$[tile16*4]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*24]+$[tile16*4+8]" -flop \) -geometry +$[tile16*5]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*25]+$[tile16*4+8]" -flop \) -geometry +$[tile16*6]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*26]+$[tile16*4+8]" -flop \) -geometry +$[tile16*7]+$[tile24*0] -composite\
 \( $DT2_png -crop "64x24+$[tile16*23]+$[tile16*10+8]" \) -geometry +$[tile16*0]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*23]+$[tile16*10+8]" -flop \) -geometry +$[tile16*4]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*24]+$[tile16*10+8]" -flop \) -geometry +$[tile16*5]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*25]+$[tile16*10+8]" -flop \) -geometry +$[tile16*6]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*26]+$[tile16*10+8]" -flop \) -geometry +$[tile16*7]+$[tile24*1] -composite\
 \( $DT2_png -crop "64x24+$[tile16*23]+$[tile16*16+8]" \) -geometry +$[tile16*0]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*23]+$[tile16*16+8]" -flop \) -geometry +$[tile16*4]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*24]+$[tile16*16+8]" -flop \) -geometry +$[tile16*5]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*25]+$[tile16*16+8]" -flop \) -geometry +$[tile16*6]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*26]+$[tile16*16+8]" -flop \) -geometry +$[tile16*7]+$[tile24*2] -composite\
 $CR_bmp

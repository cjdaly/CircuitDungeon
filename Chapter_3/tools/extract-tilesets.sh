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

ART_src=../../sourceArt
ART_dst=../dad/stuff

DC_png=$ART_src/DungeonCrawl/ProjectUtumno_full.png
DT_png=$ART_src/DungeonTileset/0x72_16x16DungeonTileset.v4.png
DT2_png=$ART_src/DungeonTilesetII/0x72_DungeonTilesetII_v1.2.png
IND_png=$ART_src/Industrial/industrial.v2.png
ADA_bmp=$ART_src/Adafruit/cp_sprite_sheet.bmp

rm -rf $ART_dst
mkdir $ART_dst


TR_bmp=$ART_dst/terrain.bmp
convert -size 64x80 xc:black $TR_bmp
convert $TR_bmp\
 \( $DT_png -crop "16x16+$[tile16*0]+$[tile16*0]" \) -geometry +$[tile16*1]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*1]+$[tile16*0]" \) -geometry +$[tile16*2]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*2]+$[tile16*0]" \) -geometry +$[tile16*3]+$[tile16*0] -composite\
 \( $DT_png -crop "16x16+$[tile16*7]+$[tile16*0]" \) -geometry +$[tile16*0]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*0]+$[tile16*1]" \) -geometry +$[tile16*1]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*1]+$[tile16*1]" \) -geometry +$[tile16*2]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*2]+$[tile16*1]" \) -geometry +$[tile16*3]+$[tile16*1] -composite\
 \( $DT_png -crop "16x16+$[tile16*12]+$[tile16*4]" \) -geometry +$[tile16*0]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*13]+$[tile16*4]" \) -geometry +$[tile16*1]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*14]+$[tile16*4]" \) -geometry +$[tile16*2]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*15]+$[tile16*4]" \) -geometry +$[tile16*3]+$[tile16*2] -composite\
 \( $DT_png -crop "16x16+$[tile16*4]+$[tile16*0]" \) -geometry +$[tile16*0]+$[tile16*3] -composite\
 \( $DT_png -crop "16x16+$[tile16*5]+$[tile16*3]" \) -geometry +$[tile16*1]+$[tile16*3] -composite\
 \( $IND_png -crop "16x16+$[tile16*5]+$[tile16*0]" \) -geometry +$[tile16*2]+$[tile16*3] -composite\
 \( $IND_png -crop "16x16+$[tile16*1]+$[tile16*5]" \) -geometry +$[tile16*3]+$[tile16*3] -composite\
 \( $IND_png -crop "16x16+$[tile16*12]+$[tile16*0]" \) -geometry +$[tile16*0]+$[tile16*4] -composite\
 \( $IND_png -crop "16x16+$[tile16*13]+$[tile16*0]" \) -geometry +$[tile16*1]+$[tile16*4] -composite\
 \( $IND_png -crop "16x16+$[tile16*14]+$[tile16*0]" \) -geometry +$[tile16*2]+$[tile16*4] -composite\
 \( $IND_png -crop "16x16+$[tile16*15]+$[tile16*0]" \) -geometry +$[tile16*3]+$[tile16*4] -composite\
 $TR_bmp


RR_bmp=$ART_dst/rugrats.bmp
convert -size 128x96 xc:transparent $RR_bmp
convert $RR_bmp\
 \( $DT2_png -crop "128x24+$[tile16*8]+$[tile16*2+8]" \) -geometry +$[tile16*0]+$[tile24*0] -composite\
 \( $DT2_png -crop "16x24+$[tile16*8]+$[tile16*2+8]" -flop \) -geometry +$[tile16*0]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*9]+$[tile16*2+8]" -flop \) -geometry +$[tile16*1]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*10]+$[tile16*2+8]" -flop \) -geometry +$[tile16*2]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*11]+$[tile16*2+8]" -flop \) -geometry +$[tile16*3]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*12]+$[tile16*2+8]" -flop \) -geometry +$[tile16*4]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*13]+$[tile16*2+8]" -flop \) -geometry +$[tile16*5]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*14]+$[tile16*2+8]" -flop \) -geometry +$[tile16*6]+$[tile24*1] -composite\
 \( $DT2_png -crop "16x24+$[tile16*15]+$[tile16*2+8]" -flop \) -geometry +$[tile16*7]+$[tile24*1] -composite\
 \( $DT2_png -crop "128x24+$[tile16*8]+$[tile16*4+8]" \) -geometry +$[tile16*0]+$[tile24*2] -composite\
 \( $DT2_png -crop "16x24+$[tile16*8]+$[tile16*4+8]" -flop \) -geometry +$[tile16*0]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*9]+$[tile16*4+8]" -flop \) -geometry +$[tile16*1]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*10]+$[tile16*4+8]" -flop \) -geometry +$[tile16*2]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*11]+$[tile16*4+8]" -flop \) -geometry +$[tile16*3]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*12]+$[tile16*4+8]" -flop \) -geometry +$[tile16*4]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*13]+$[tile16*4+8]" -flop \) -geometry +$[tile16*5]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*14]+$[tile16*4+8]" -flop \) -geometry +$[tile16*6]+$[tile24*3] -composite\
 \( $DT2_png -crop "16x24+$[tile16*15]+$[tile16*4+8]" -flop \) -geometry +$[tile16*7]+$[tile24*3] -composite\
 $RR_bmp


PET_bmp=$ART_dst/pets.bmp
convert -size 256x64 xc:black $PET_bmp
convert $PET_bmp\
 \( $DC_png -crop "32x32+$[tile32*1]+$[tile32*94]" \) -geometry +$[tile32*0]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*2]+$[tile32*94]" \) -geometry +$[tile32*1]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*4]+$[tile32*94]" \) -geometry +$[tile32*2]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*94]" \) -geometry +$[tile32*3]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*7]+$[tile32*94]" \) -geometry +$[tile32*4]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*8]+$[tile32*94]" \) -geometry +$[tile32*5]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*9]+$[tile32*94]" \) -geometry +$[tile32*6]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*10]+$[tile32*94]" \) -geometry +$[tile32*7]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*40]+$[tile32*84]" \) -geometry +$[tile32*0]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*41]+$[tile32*84]" \) -geometry +$[tile32*1]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*42]+$[tile32*84]" \) -geometry +$[tile32*2]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*43]+$[tile32*84]" \) -geometry +$[tile32*3]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*44]+$[tile32*84]" \) -geometry +$[tile32*4]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*56]+$[tile32*77]" \) -geometry +$[tile32*5]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*19]+$[tile32*94]" \) -geometry +$[tile32*6]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*31]+$[tile32*12]" \) -geometry +$[tile32*7]+$[tile32*1] -composite\
 $PET_bmp


SNK_bmp=$ART_dst/snacks.bmp
convert -size 256x64 xc:black $SNK_bmp
convert $SNK_bmp\
 \( $DC_png -crop "32x32+$[tile32*31]+$[tile32*40]" \) -geometry +$[tile32*0]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*32]+$[tile32*40]" \) -geometry +$[tile32*1]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*1]+$[tile32*40]" \) -geometry +$[tile32*2]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*4]+$[tile32*40]" \) -geometry +$[tile32*3]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*6]+$[tile32*40]" \) -geometry +$[tile32*4]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*16]+$[tile32*40]" \) -geometry +$[tile32*5]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*38]+$[tile32*40]" \) -geometry +$[tile32*6]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*39]+$[tile32*40]" \) -geometry +$[tile32*7]+$[tile32*0] -composite\
 \( $DC_png -crop "32x32+$[tile32*0]+$[tile32*42]" \) -geometry +$[tile32*0]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*3]+$[tile32*42]" \) -geometry +$[tile32*1]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*5]+$[tile32*42]" \) -geometry +$[tile32*2]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*8]+$[tile32*42]" \) -geometry +$[tile32*3]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*10]+$[tile32*42]" \) -geometry +$[tile32*4]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*11]+$[tile32*42]" \) -geometry +$[tile32*5]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*25]+$[tile32*42]" \) -geometry +$[tile32*6]+$[tile32*1] -composite\
 \( $DC_png -crop "32x32+$[tile32*28]+$[tile32*42]" \) -geometry +$[tile32*7]+$[tile32*1] -composite\
 $SNK_bmp

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

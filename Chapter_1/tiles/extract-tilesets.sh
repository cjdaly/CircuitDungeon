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
tile32=32
SRC_art=../../sourceArt
DT_png=$SRC_art/DungeonTileset/0x72_16x16DungeonTileset.v4.png
DT2_png=$SRC_art/DungeonTilesetII/0x72_DungeonTilesetII_v1.2.png
IND_png=$SRC_art/Industrial/industrial.v2.png

rm -rf terrain heroes creatures objects misc
mkdir terrain
mkdir creatures
mkdir heroes
mkdir objects
mkdir misc

# Dungeon Tileset
#
convert $DT_png -crop "16x16+$[tile16*3]+$[tile16*0]" terrain/wall_pipe_low.bmp
convert $DT_png -crop "16x16+$[tile16*4]+$[tile16*0]" terrain/wall_pipe_high.bmp
convert $DT_png -crop "16x16+$[tile16*5]+$[tile16*3]" terrain/wall_pipe_mid.bmp
convert $DT_png -crop "16x16+$[tile16*7]+$[tile16*0]" terrain/wall_grate_mid.bmp
convert $DT_png -crop "16x16+$[tile16*4]+$[tile16*1]" terrain/wall_grate_low.bmp
convert $DT_png -crop "16x16+$[tile16*4]+$[tile16*2]" terrain/wall_step_right.bmp
convert $DT_png -crop "16x16+$[tile16*4]+$[tile16*3]" terrain/wall_step_left.bmp
convert $DT_png -crop "16x16+$[tile16*4]+$[tile16*6]" terrain/wall_black.bmp
convert $DT_png -crop "16x16+$[tile16*1]+$[tile16*1]" terrain/wall4.bmp

convert $DT_png -crop "16x16+$[tile16*1]+$[tile16*3]" objects/skull1.bmp
convert $DT_png -crop "128x32+$[tile16*7]+$[tile16*2]" objects/sword_big.bmp
convert $DT_png -crop "32x16+$[tile16*8]+$[tile16*6]" objects/sword_small.bmp


# Dungeon Tileset II
#
convert $DT2_png -crop "64x24+$[tile16*8]+$[tile32*0+8]" heroes/knave_fe.bmp
convert $DT2_png -crop "64x24+$[tile16*8]+$[tile32*1+8]" heroes/knave_ma.bmp
convert $DT2_png -crop "64x24+$[tile16*8]+$[tile32*2+8]" heroes/knight_fe.bmp
convert $DT2_png -crop "64x24+$[tile16*8]+$[tile32*3+8]" heroes/knight_ma.bmp
convert $DT2_png -crop "64x24+$[tile16*8]+$[tile32*4+8]" heroes/wizard_fe.bmp
convert $DT2_png -crop "64x24+$[tile16*8]+$[tile32*5+8]" heroes/wizard_ma.bmp

convert $DT2_png -crop "64x24+$[tile16*23]+$[tile32*2+8]" heroes/knave_un.bmp
convert $DT2_png -crop "64x24+$[tile16*23]+$[tile32*5+8]" heroes/knight_un.bmp
convert $DT2_png -crop "64x24+$[tile16*23]+$[tile32*8+8]" heroes/wizard_un.bmp

convert $DT2_png -crop "64x24+$[tile16*23]+$[tile32*4+8]" creatures/stoney.bmp
convert $DT2_png -crop "64x24+$[tile16*27]+$[tile32*4+8]" creatures/frosty.bmp
convert $DT2_png -crop "64x24+$[tile16*27]+$[tile32*3+8]" creatures/swamper.bmp
convert $DT2_png -crop "64x24+$[tile16*23]+$[tile32*10+8]" creatures/nibbler.bmp
convert $DT2_png -crop "64x48+$[tile16*23]+$[tile16*1]" creatures/blip.bmp
convert $DT2_png -crop "128x32+$[tile16*1]+$[tile16*17]" creatures/ogre.bmp
convert $DT2_png -crop "128x32+$[tile16*1]+$[tile16*20]" creatures/troll.bmp
convert $DT2_png -crop "128x32+$[tile16*1]+$[tile16*23]" creatures/gnasher.bmp

convert $DT2_png -crop "16x16+$[tile16*14]+$[tile16*14]" objects/skull2.bmp
convert $DT2_png -crop "64x16+$[tile16*18]+$[tile16*14]" objects/potion.bmp
convert $DT2_png -crop "64x16+$[tile16*18]+$[tile16*15]" objects/vial.bmp
convert $DT2_png -crop "48x48+$[tile16*15]+$[tile16*13]" objects/chest.bmp
convert $DT2_png -crop "64x16+$[tile16*1]+$[tile16*12]" objects/button.bmp
convert $DT2_png -crop "32x16+$[tile16*5]+$[tile16*12]" objects/switch1.bmp
convert $DT2_png -crop "32x16+$[tile16*18]+$[tile16*17]" misc/coin.bmp
convert $DT2_png -crop "48x16+$[tile16*18]+$[tile16*16]" misc/heart.bmp


convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*1]" terrain/wall1.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*10]" terrain/wall2.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*10]" terrain/wall3.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*2]" terrain/wall_banner_red.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*2]" terrain/wall_banner_blue.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*3]" terrain/wall_banner_green.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*3]" terrain/wall_banner_yellow.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*2]" terrain/wall_hole_left.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*3]" terrain/wall_hole_right.bmp


# Industrial
#

convert $IND_png -crop "16x16+$[tile16*1]+$[tile16*5]" terrain/platform_a1.bmp

convert $IND_png -crop "16x16+$[tile16*4]+$[tile16*6]" terrain/platform_f1.bmp
convert $IND_png -crop "16x16+$[tile16*5]+$[tile16*6]" terrain/platform_f2.bmp
convert $IND_png -crop "16x16+$[tile16*6]+$[tile16*6]" terrain/platform_f3.bmp
convert $IND_png -crop "16x16+$[tile16*7]+$[tile16*6]" terrain/platform_f4.bmp
convert $IND_png -crop "16x16+$[tile16*8]+$[tile16*6]" terrain/platform_f5.bmp
convert $IND_png -crop "16x16+$[tile16*9]+$[tile16*6]" terrain/platform_f6.bmp

convert $IND_png -crop "16x16+$[tile16*5]+$[tile16*0]" terrain/platform_x1.bmp
convert $IND_png -crop "16x16+$[tile16*12]+$[tile16*0]" terrain/platform_x2.bmp
convert $IND_png -crop "16x16+$[tile16*13]+$[tile16*0]" terrain/platform_x3.bmp
convert $IND_png -crop "16x16+$[tile16*14]+$[tile16*0]" terrain/platform_x4.bmp
convert $IND_png -crop "16x16+$[tile16*15]+$[tile16*0]" terrain/platform_x5.bmp
convert $IND_png -crop "16x16+$[tile16*19]+$[tile16*0]" terrain/platform_x6.bmp
convert $IND_png -crop "16x16+$[tile16*20]+$[tile16*0]" terrain/platform_x7.bmp
convert $IND_png -crop "16x16+$[tile16*21]+$[tile16*0]" terrain/platform_x8.bmp

convert $IND_png -crop "64x32+$[tile16*0]+$[tile16*6]" objects/tube.bmp
convert $IND_png -crop "80x16+$[tile16*5]+$[tile16*8]" objects/switch2.bmp
convert $IND_png -crop "64x16+$[tile16*4]+$[tile16*10]" misc/bars.bmp
convert $IND_png -crop "128x16+$[tile16*21]+$[tile16*9]" misc/status.bmp

convert $IND_png -crop "64x16+$[tile16*0]+$[tile16*17]" heroes/knave_si.bmp
convert $IND_png -crop "64x16+$[tile16*0]+$[tile16*23]" heroes/knight_si.bmp
convert $IND_png -crop "64x16+$[tile16*0]+$[tile16*25]" heroes/wizard_si.bmp

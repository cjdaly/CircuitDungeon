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
DC_png=../DungeonCrawl/ProjectUtumno_full.png
DT2_png=../DungeonTilesetII/0x72_DungeonTilesetII_v1.2.png

rm -rf tileset1
mkdir tileset1

convert $DT2_png -crop "16x24+$[tile16*8]+$[tile32*0+8]" tileset1/elf_f.bmp
convert $DT2_png -crop "16x24+$[tile16*8]+$[tile32*1+8]" tileset1/elf_m.bmp
convert $DT2_png -crop "16x24+$[tile16*8]+$[tile32*2+8]" tileset1/knight_f.bmp
convert $DT2_png -crop "16x24+$[tile16*8]+$[tile32*3+8]" tileset1/knight_m.bmp
convert $DT2_png -crop "16x24+$[tile16*8]+$[tile32*4+8]" tileset1/wiz_f.bmp
convert $DT2_png -crop "16x24+$[tile16*8]+$[tile32*5+8]" tileset1/wiz_m.bmp

convert $DT2_png -crop "16x24+$[tile16*23]+$[tile32*2+8]" tileset1/npc_skeleton.bmp
convert $DT2_png -crop "16x24+$[tile16*23]+$[tile32*5+8]" tileset1/npc_masked.bmp
convert $DT2_png -crop "16x24+$[tile16*23]+$[tile32*8+8]" tileset1/npc_cloaked.bmp

convert $DT2_png -crop "16x16+$[tile16*14]+$[tile16*14]" tileset1/skull.bmp
convert $DT2_png -crop "16x16+$[tile16*15]+$[tile16*14]" tileset1/chest_closed.bmp
convert $DT2_png -crop "16x16+$[tile16*17]+$[tile16*14]" tileset1/chest_open.bmp

convert $DT2_png -crop "16x16+$[tile16*18]+$[tile16*14]" tileset1/potion_red.bmp
convert $DT2_png -crop "16x16+$[tile16*19]+$[tile16*14]" tileset1/potion_blue.bmp
convert $DT2_png -crop "16x16+$[tile16*20]+$[tile16*14]" tileset1/potion_green.bmp
convert $DT2_png -crop "16x16+$[tile16*21]+$[tile16*14]" tileset1/potion_yellow.bmp

convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*1]" tileset1/wall_left.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*1]" tileset1/wall_mid.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*10]" tileset1/wall_mid2.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*10]" tileset1/wall_mid3.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*1]" tileset1/wall_right.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*2]" tileset1/wall_banner_red.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*2]" tileset1/wall_banner_blue.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*3]" tileset1/wall_banner_green.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*3]" tileset1/wall_banner_yellow.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*2]" tileset1/wall_hole1.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*3]" tileset1/wall_hole2.bmp
convert $DT2_png -crop "16x16+$[tile16*4]+$[tile16*5]" tileset1/wall_goo.bmp

convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*0]" tileset1/walltop_left.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*0]" tileset1/walltop_mid.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*0]" tileset1/walltop_right.bmp
convert $DT2_png -crop "16x16+$[tile16*0]+$[tile16*7]" tileset1/walltop_R4.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*7]" tileset1/walltop_L4.bmp
convert $DT2_png -crop "16x16+$[tile16*0]+$[tile16*8]" tileset1/walltop_R1.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*8]" tileset1/walltop_L1.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*8]" tileset1/walltop_L2.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*8]" tileset1/walltop_R2.bmp
convert $DT2_png -crop "16x16+$[tile16*0]+$[tile16*9]" tileset1/walltop_R3.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*9]" tileset1/walltop_L3.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*9]" tileset1/walltop_LL.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*9]" tileset1/walltop_LR.bmp

convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*4]" tileset1/floor1.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*4]" tileset1/floor2.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*4]" tileset1/floor3.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*5]" tileset1/floor4.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*5]" tileset1/floor5.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*5]" tileset1/floor6.bmp
convert $DT2_png -crop "16x16+$[tile16*1]+$[tile16*6]" tileset1/floor7.bmp
convert $DT2_png -crop "16x16+$[tile16*2]+$[tile16*6]" tileset1/floor8.bmp
convert $DT2_png -crop "16x16+$[tile16*3]+$[tile16*6]" tileset1/floor_ladder.bmp
convert $DT2_png -crop "16x16+$[tile16*4]+$[tile16*6]" tileset1/floor_goo.bmp
convert $DT2_png -crop "16x16+$[tile16*6]+$[tile16*8]" tileset1/floor_wall.bmp
convert $DT2_png -crop "16x16+$[tile16*6]+$[tile16*9]" tileset1/floor_hole.bmp
convert $DT2_png -crop "16x16+$[tile16*5]+$[tile16*11]" tileset1/floor_stairs.bmp

convert $DT2_png -crop "64x48+$[tile16*1]+$[tile16*13]" tileset1/gateway.bmp


convert $DC_png -crop "32x32+$[tile32*13]+$[tile32*13]" tileset1/tree1.bmp
convert $DC_png -crop "32x32+$[tile32*14]+$[tile32*13]" tileset1/tree2.bmp
convert $DC_png -crop "32x32+$[tile32*15]+$[tile32*13]" tileset1/tree3.bmp
convert $DC_png -crop "32x32+$[tile32*16]+$[tile32*13]" tileset1/tree4.bmp

convert $DC_png -crop "32x32+$[tile32*27]+$[tile32*12]" tileset1/statue_at.bmp
convert $DC_png -crop "32x32+$[tile32*31]+$[tile32*12]" tileset1/statue_cat.bmp
convert $DC_png -crop "32x32+$[tile32*39]+$[tile32*12]" tileset1/statue_bat.bmp



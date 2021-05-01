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

import board, neopixel
import displayio, terminalio
import random, time

def load_tilegrid(flName,w,h,tw,th):
  f = open("/dungeon/tiles/" + flName + ".bmp", "rb")
  odb = displayio.OnDiskBitmap(f)
  tg=displayio.TileGrid(odb, pixel_shader=displayio.ColorConverter(), width=w, height=h, tile_width=tw, tile_height=th)
  return tg

def init_tilegrid(data,flName,tgList, w,h,tw,th, x,y, grp='GRP'):
  tg=load_tilegrid(flName, w,h,tw,th)
  tg.x=x ; tg.y=y
  data[grp].append(tg) ; tgList.append(tg)
  return tg

def init_creature(data,flName,tgList, w=1,h=1,tw=16,th=24,x=-99,y=-99):
  tg=init_tilegrid(data,flName,tgList, w,h,tw,th,x,y, 'GRP_CR')

def init():
  DSP=board.DISPLAY
  data={} ; data['terrainMap']={} ; i=0
  for c in ' (_)"[#]RGBYOoX^CDEF':
    data['terrainMap'][c]=i ; i+=1
  #
  data['GRP']=displayio.Group(max_size=4)
  data['GRP_CR']=displayio.Group(max_size=6, scale=2)
  #
  tgMaps=[] ; data['tgMaps']=tgMaps
  w=DSP.width//16 ; data['MAP_w']=w
  h=DSP.height//16 ; data['MAP_h']=h
  init_tilegrid(data,"terrain",tgMaps, w,h,16,16,DSP.width,0)
  init_tilegrid(data,"terrain",tgMaps, w,h,16,16,DSP.width,0)
  #
  tgHeroes=[] ; data['tgHeroes']=tgHeroes
  init_creature(data,"heroes",tgHeroes)
  init_creature(data,"heroes",tgHeroes)
  init_creature(data,"heroes",tgHeroes)
  data['tgHeroAttrs']=["0rr", "1rr", "2rr"]
  #
  tgNasties=[] ; data['tgNasties']=tgNasties
  init_creature(data,"nasties",tgNasties)
  init_creature(data,"nasties",tgNasties)
  init_creature(data,"nasties",tgNasties)
  data['tgNastyAttrs']=["0rr", "1rr", "2rr"]
  #
  data['GRP'].append(data['GRP_CR'])
  DSP.show(data['GRP'])
  #
  data['NeoPix']=neopixel.NeoPixel(board.NEOPIXEL,1,brightness=0.5)
  #
  return data

# creature attributes
# 0: creature index digit: '0'-'2'
# 1: 'r'=face right ; 'l'=face left
# 2: 'r'=run ; 'w'=walk ; 'f'=fall/jump
def creatureTile(attrs, cFrame, nTiles=9):
  idx=0
  if attrs[0]=='2':
    idx=nTiles*4
  elif attrs[0]=='1':
    idx=nTiles*2
  #
  if attrs[1]=='l':
    idx+=nTiles
  #
  if attrs[2]=='w':
    idx+=cFrame
  elif attrs[2]=='r':
    idx+=cFrame+4
  elif nTiles==9:
    idx+=8
  #
  return idx

def showCreature(data, tg, xOffset):
  DSP=board.DISPLAY
  tg.x=DSP.width//4 - 16 + xOffset
  tg.y=(DSP.height - data['elev']*16)//2 - 20

def sceneReset(data, phase, cFrame, cTurn, cScene):
  DSP=board.DISPLAY
  #
  i=1
  for tg in data['tgMaps']:
    tg.x=DSP.width*i ; i+=1
  for tg in data['tgHeroes']:
    tg.y=-99
  for tg in data['tgNasties']:
    tg.y=-99
  #
  data['elev']=4 ; data['ceil']=12 ; data['velo']=-2 ; 
  data['nextScene']=""
  #
  showCreature(data, data['tgHeroes'][0], 0)
  #showCreature(data, data['tgHeroes'][1], 20)
  #showCreature(data, data['tgHeroes'][2], -20)
  #
  #showCreature(data, data['tgNasties'][0], 0)
  #showCreature(data, data['tgNasties'][1], 0)
  #showCreature(data, data['tgNasties'][2], 0)

def sceneCycle(data, phase, cFrame, cTurn, cScene):
  DSP=board.DISPLAY
  #
  v=data['velo']
  for tgMap in data['tgMaps']:
    if tgMap.x<=-DSP.width:
      tgMap.x=DSP.width
    #
    if tgMap.x<=0 or tgMap.x>DSP.width:
      tgMap.x+=v
    else:
      if tgMap.x%16==0:
        mapX=(DSP.width-tgMap.x)//16
        mapY=data['MAP_h']
        elev=data['elev'] ; ceil=data['ceil']
        while mapY>=1:
          mapY-=1 ; ceil-=1
          if elev<=0:
            if ceil==-1 and cTurn%8==0:
              tgMap[mapX,mapY]=random.randint(8,11)
            elif ceil<=0:
              tgMap[mapX,mapY]=6
            else:
              tgMap[mapX,mapY]=0
          elif elev==1:
            tgMap[mapX,mapY]=2
          elif elev==2:
            tgMap[mapX,mapY]=6
          else:
            r=random.randint(0,33)
            if r==0:
              tgMap[mapX,mapY]=4
            elif r==1:
              tgMap[mapX,mapY]=12
            elif r==2:
              tgMap[mapX,mapY]=13
            else:
              tgMap[mapX,mapY]=6
          elev-=1
      tgMap.x+=v
  #
  data['NeoPix'][0]=(0,0,cFrame*4)
  #
  i=0
  for tgHero in data['tgHeroes']:
    if tgHero.y!=-99:
      tgHero[0,0]=creatureTile(data['tgHeroAttrs'][i], cFrame)
    i+=1
  i=0
  for tgNasty in data['tgNasties']:
    if tgNasty.y!=-99:
      tgNasty[0,0]=creatureTile(data['tgNastyAttrs'][i], cFrame, 8)
    i+=1
  #
  data['NeoPix'][0]=(0,0,cFrame*4+2)

def play(data=None):
  phase=""
  if not data:
    data = init()
  cFrame = -1 ; cTurn = 0 ; cScene = 0 ; done = False
  #
  sceneReset(data, phase, cFrame, cTurn, cScene)
  while not done:
    cFrame+=1
    if cFrame>3:
      cFrame=0 ; cTurn+=1
    #
    sceneCycle(data, phase, cFrame, cTurn, cScene)
    if data['nextScene'] != "":
      cScene+=1 ; cTurn=0
      sceneReset(data, phase, cFrame, cTurn, cScene)
    #
  return data


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

# ChompCode - code with a bigger byte

import re, random

def init(game):
  CCPU={} ; game['CCPU']=CCPU
  NOMS={} ; CCPU['NOMS']=NOMS
  NOMS['SUPs']=[] # run at beginning of joke
  NOMS['noms']=[] # run before every frame
  NOMS['NOMs']=[] # after wait_for_frame()
  NOMS['Noms']=[] # start of turn (frame 0 of 4)
  NOMS['nOms']=[] # middle of turn (frame 1)
  NOMS['NoMs']=[] # middle of turn (frame 2)
  NOMS['noMs']=[] # end of turn (frame 3)
  NOMS['SDNs']=[] # run at end of joke
  CCPU['decodeNom']=re.compile('(\w+)\s*\(([^)]*)\)')
  CCPU['decodeYo']=re.compile('(\w+)[=:](.*)')
  #
  MAP=[] ; CCPU['MAP']=MAP
  REGS={} ; CCPU['REGS']=REGS
  YOS={} ; CCPU['YOS']=YOS
  #
  OPS={} ; CCPU['OPS']=OPS
  OPS['setTopText']=CC_setTopText
  OPS['setBottomText']=CC_setBottomText
  OPS['setMiddleText']=CC_setMiddleText
  OPS['hideText']=CC_hideText
  OPS['playerPosition']=CC_playerPosition
  OPS['playerMove']=CC_playerMove
  OPS['playerMorph']=CC_playerMorph
  OPS['randomap']=CC_randomap
  OPS['levelExit']=CC_levelExit
  return CCPU

def TM(game,c):
  if c in game['terrMap']:
    return game['terrMap'][c]
  else:
    return 8 # red flag

def reset_CCPU(CCPU):
  NOMS=CCPU['NOMS'];
  NOMS['SUPs'].clear() ; NOMS['SDNs'].clear()
  NOMS['noms'].clear() ; NOMS['NOMs'].clear()
  NOMS['Noms'].clear() ; NOMS['nOms'].clear()
  NOMS['NoMs'].clear() ; NOMS['noMs'].clear()
  CCPU['MAP'].clear() ; CCPU['REGS'].clear() ; CCPU['YOS'].clear()

def load_joke(game, CCPU, joke):
  reset_CCPU(CCPU)
  with open("/dad/jokes/" + joke + ".dad") as f:
    for line in f:
      if line.startswith("/"):
        CCPU['MAP'].append(line[1:11])
      elif line[:4].lower()=='nom:':
        CCPU['NOMS'][line[:3]+'s'].append(line[4:].rstrip())
      elif line[:4].lower()=='sup:':
        CCPU['NOMS']['SUPs'].append(line[4:].rstrip())
      elif line[:4].lower()=='sdn:':
        CCPU['NOMS']['SDNs'].append(line[4:].rstrip())
      elif line[:3].lower()=='yo:':
        k,v=CCPU['decodeYo'].match(line[3:].rstrip()).groups()
        CCPU['YOS'][k]=v
  # update tilegrid
  for y in range(6):
    for x in range(10):
      game['jokeRoom'][x,y]=TM(game, CCPU['MAP'][y][x])

##

def decode_param(game, CCPU, pL, pD, param):
  c=param[0]
  if c.isdigit() or c=='-':
    if '.' in param:
      return float(param)
    else:
      return int(param)
  elif c.isalpha():
    return game[param]
  elif c=='~':
    return param[1:]
  elif c=='&':
    if param=="&&":
      return CCPU['REGS']
    else:
      return CCPU['REGS'][param[1:]]
  elif c=='$':
    if param=="$$":
      return CCPU['YOS']
    else:
      return CCPU['YOS'][param[1:]]
  elif c=='@':
    if param=="@@":
      return pL
    elif param=="@FR":
      return pL[0]
    elif param=="@TR":
      return pL[1]
    elif param=="@LV":
      return pL[2]
    elif param=="@GP":
      return pL[3]
    elif param[1].isdigit():
      return pL[int(param[1:])]
  elif c=='#':
    if param=="##":
      return pD
    else:
      return pD[param[1:]]
  return None

def decode_eval(game, CCPU, pL, pD, nom):
  op, params = CCPU['decodeNom'].match(nom).groups()
  paramList=[]
  for p in params.split(','):
    paramList.append(decode_param(game,CCPU,pL,pD,p.strip()))
  CCPU['OPS'][op](*paramList)

def eval_noms(phase, game, CCPU, pL, pD):
  for nom in CCPU['NOMS'][phase]:
    decode_eval(game, CCPU, pL, pD, nom)

##

def HH_showTextTG(DSP,tilegrid,text,color,x,y):
  tilegrid.x=x ; tilegrid.y=y
  tilegrid.text=text ; tilegrid.color=color
  DSP.wait_for_frame()

def HH_hideTextTG(DSP,tilegrid,y):
  tilegrid.y = y
  DSP.wait_for_frame()

def HH_playerMove(playerTG, mapTG, x, mapY=4):
  xNew=playerTG.x + x ; mapXNew = xNew // 16 ; mapXOff = xNew % 16
  if x > 0: # moving right
    if mapXOff > 0:
      mapXNew+=1
  if mapTG[mapXNew,mapY] > 3: # blocked, bounce
    xNew = playerTG.x - x
  playerTG.x = xNew

##

def CC_setTopText(DSP,tilegrid,text,color=0xFF00FF):
  HH_showTextTG(DSP,tilegrid,text,color,1,7)

def CC_setBottomText(DSP,tilegrid,text,hide=False,color=0x00FFFF):
  HH_showTextTG(DSP,tilegrid,text,color,1,119)

def CC_setMiddleText(DSP,tilegrid,text,hide=False,color=0xFFFF00):
  HH_showTextTG(DSP,tilegrid,text,color,8,58)

def CC_hideText(DSP,tilegrid,y=-33):
  HH_hideTextTG(DSP,tilegrid,y)

def CC_playerPosition(DSP,rugrat,x,y,isRel):
  if isRel:
    rugrat.x+=x ; rugrat.y+=y
  else:
    rugrat.x=x ; rugrat.y=y
  DSP.wait_for_frame()

def CC_playerMove(rugrat,jokeRoom,iFR,pD):
  if pD['faceRight']:
    if pD['onTheMove']:
      pD['onTheMove']=False
      HH_playerMove(rugrat,jokeRoom, 4)
      rugrat[0,0]=pD['spriteBase']+iFR+4
    else:
      rugrat[0,0]=pD['spriteBase']+iFR
  else:
    if pD['onTheMove']:
      pD['onTheMove']=False
      HH_playerMove(rugrat,jokeRoom, -4)
      rugrat[0,0]=pD['spriteBase']+iFR+12
    else:
      rugrat[0,0]=pD['spriteBase']+iFR+8

def CC_playerMorph(iGP,pD):
  if iGP==1:
    if pD['spriteBase'] == 0:
      pD['spriteBase']=16
    else:
      pD['spriteBase']=0
  elif iGP==16:
    if pD['faceRight']:
      pD['onTheMove']=True
    else:
      pD['faceRight']=True
  elif iGP==128:
    if not pD['faceRight']:
      pD['onTheMove']=True
    else:
      pD['faceRight']=False

def CC_randomap(mapTG,x,y,min,max,prob=4):
  if random.randint(1,prob)==1:
    mapTG[x,y]=random.randint(min,max)

def CC_levelExit(game,rugrat,onMapX,nextJokeHint,mapXModMin=4,mapXModMax=11):
  mapX = rugrat.x // 16 ; mapXMod = rugrat.x % 16
  if mapX == onMapX:
    if mapXMod>=mapXModMin and mapXMod<=mapXModMax:
      CCPU=game['CCPU'] ; pL=game['pL'] ; pD=game['pD']
      eval_noms('SDNs', game, CCPU, pL, pD)
      load_joke(game, CCPU, nextJokeHint)
      pL[1]=0 ; pL[2]+=1
      eval_noms('SUPs', game, CCPU, pL, pD)


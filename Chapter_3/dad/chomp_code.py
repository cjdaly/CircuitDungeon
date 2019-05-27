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

import re

def init(game):
  CCPU={} ; game['CCPU']=CCPU
  NOMS={} ; CCPU['NOMS']=NOMS
  NOMS['noms']=[] # run before every frame
  NOMS['NOMs']=[] # after wait_for_frame()
  NOMS['Noms']=[] # start of turn (frame 0 of 4)
  NOMS['nOms']=[] # middle of turn (frame 1)
  NOMS['NoMs']=[] # middle of turn (frame 2)
  NOMS['noMs']=[] # end of turn (frame 3)
  CCPU['decodeNom']=re.compile('(\w+)\s*\(([^)]*)\)')
  CCPU['decodeYo']=re.compile('(\w+)=(.*)')
  #
  MAP=[] ; CCPU['MAP']=MAP
  REGS={} ; CCPU['REGS']=REGS
  YOS={} ; CCPU['YOS']=YOS
  #
  OPS={} ; CCPU['OPS']=OPS
  OPS['anim1']=CC_anim1
  return CCPU

def TM(game,c):
  if c in game['terrMap']:
    return game['terrMap'][c]
  else:
    return 8 # red flag

def reset_CCPU(CCPU):
  NOMS=CCPU['NOMS'];
  NOMS['nom'].clear() ; NOMS['NOM'].clear()
  NOMS['Nom'].clear() ; NOMS['nOm'].clear()
  NOMS['NoM'].clear() ; NOMS['noM'].clear()
  CCPU['MAP'].clear()
  CCPU['REGS'].clear()
  CCPU['YOS'].clear()

def load_joke(game, CCPU, joke):
  reset_CCPU(CCPU)
  with open("/dad/jokes/" + joke + ".dad") as f:
    for line in f:
      if line.startswith("/"):
        CCPU['MAP'].append(line[1:11])
      elif line[:4].lower()=='nom:':
        CCPU['NOMS'][line[:3]].append(line[4:].rstrip())
      elif line[:3].lower()=='yo:':
        k,v=CCPU['decodeYo'].match(line[3:].rstrip()).groups()
        CCPU['YOS'][k]=v
      elif line.startswith(":T:"):
        game['textT'].text=line[3:].rstrip()
      elif line.startswith(":M:"):
        game['textM'].text=line[3:].rstrip()
      elif line.startswith(":B:"):
        game['textB'].text=line[3:].rstrip()
  # update tilegrid
  for y in range(6):
    for x in range(10):
      game['jokeRoom'][x,y]=TM(game, CCPU['MAP'][y][x])

##

def decode_param(game, CCPU, pL, pD, param):
  c=param[0]
  if c.isdigit():
    if '.' in param:
      return float(param)
    else:
      return int(param)
  elif c.isalpha():
    return game[param]
  elif c=='$':
    if param=="$$":
      return CCPU['REGS']
    else:
      return CCPU['REGS'][param[1:]]
  elif c=='@':
    if param=="@FR":
      return pL[0]
    elif param=="@TR":
      return pL[1]
    elif param=="@LV":
      return pL[2]
    elif param[1].isdigit():
      return pL[int(param[1:])]
  elif c=='#':
    return pD[param[1:]]
  else:
    return None

def decode_eval(game, CCPU, pL, pD, nom):
  op, params = CCPU['decodeNom'].match(nom).groups()
  paramList=[]
  for p in params.split(','):
    paramList.append(decode_param(game,CCPU,pL,pD,p.strip()))
  CCPU['OPS'][op](*paramList)

def pre_frame(game, CCPU, pL, pD):
  for nom in CCPU['NOMS']['noms']:
    decode_eval(game, CCPU, pL, pD, nom)

def frame(game, CCPU, pL, pD):
  fCount=pL[0] ; NOMS=CCPU['NOMS']
  noms=None
  if fCount==0:
    noms=NOMS['Noms']
  elsif fCount==1:
    noms=NOMS['nOms']
  elsif fCount==2:
    noms=NOMS['NoMs']
  elsif fCount==3:
    noms=NOMS['noMs']
  #
  for nom in noms:
    decode_eval(game, CCPU, pL, pD, nom)

def post_frame(game, CCPU, pL, pD):
  for nom in CCPU['NOMS']['NOMs']:
    decode_eval(game, CCPU, pL, pD, nom)

#

def CC_anim1(rugrat, iFR):
  rugrat[0,0]=iFR


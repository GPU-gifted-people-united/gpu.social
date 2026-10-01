#!/usr/bin/env python3
"""Optional development helper (Pillow): draw the site's social preview."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import math
ROOT=Path(__file__).resolve().parents[1]
FONT=Path('/System/Library/Fonts/Supplemental')
im=Image.new('RGB',(1200,630),'#0c1b25');d=ImageDraw.Draw(im)
def font(name,size):return ImageFont.truetype(str(FONT/name),size)
def line(points,fill='#455654',width=1):d.line(points,fill=fill,width=width)
for r in [150,180,205]:d.ellipse((880-r,300-r,880+r,300+r),outline='#394b4f',width=1)
line([(670,300),(1090,300)]);line([(880,90),(880,510)])
for i in range(0,360,15):
 a=math.radians(i);x,y=880+220*math.cos(a),300+220*math.sin(a);d.ellipse((x-1,y-1,x+1,y+1),fill='#82918c')
d.polygon([(880,165),(896,284),(1015,300),(896,316),(880,435),(864,316),(745,300),(864,284)],outline='#d6ac76',fill='#192c35')
for points in [[(880,165),(880,300),(896,284)],[(880,435),(880,300),(864,316)],[(745,300),(880,300),(864,284)],[(1015,300),(880,300),(896,316)]]:d.polygon(points,fill='#d6ac76')
d.ellipse((872,292,888,308),fill='#d6ac76')
line([(730,180),(780,140),(816,200),(750,230),(730,180)],'#82918c')
for x,y in [(730,180),(780,140),(816,200),(750,230)]:d.ellipse((x-3,y-3,x+3,y+3),fill='#ccd4cc')
d.text((70,55),'gpu',font=font('Arial Bold.ttf',56),fill='#f1eee5');d.text((190,63),'✳',font=font('Arial.ttf',36),fill='#d6ac76')
d.text((70,165),'Explore.',font=font('Georgia.ttf',65),fill='#f1eee5')
d.text((70,245),'Create.',font=font('Georgia.ttf',65),fill='#f1eee5')
d.text((70,325),'Participate.',font=font('Georgia Italic.ttf',65),fill='#d6ac76')
d.rectangle((0,550,1200,630),fill='#f1eee5')
d.text((70,576),'Gifted People United',font=font('Arial.ttf',24),fill='#101f29')
d.text((970,578),'gpu.social',font=font('Arial.ttf',22),fill='#101f29')
im.save(ROOT/'public/social.png')

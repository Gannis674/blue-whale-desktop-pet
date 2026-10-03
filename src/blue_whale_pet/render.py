"""Articulated artwork rendered at the display refresh timer, with real alpha."""
from pathlib import Path
import math
from PIL import Image
from PySide6.QtCore import QRectF
from PySide6.QtGui import QImage, QPixmap

HERE=Path(__file__).resolve().parent/'assets'

def load_part(path,box=None,upper_only=False,isolate=False):
    with Image.open(path) as image:
        image=image.convert('RGBA')
        if box:
            image=image.crop(box)
        if isolate:
            # Atlas decoding: ignore detached neighboring fragments in a cell.
            w,h=image.size
            bits=bytearray(image.getchannel('A').point(lambda a:255 if a>35 else 0).tobytes())
            largest=[]
            for seed in range(len(bits)):
                if not bits[seed]:
                    continue
                stack=[seed]
                bits[seed]=0
                component=[]
                while stack:
                    k=stack.pop()
                    component.append(k)
                    x=k%w
                    for neighbor in ((k-1 if x else -1),(k+1 if x<w-1 else -1),k-w,k+w):
                        if 0<=neighbor<len(bits) and bits[neighbor]:
                            bits[neighbor]=0
                            stack.append(neighbor)
                if len(component)>len(largest):
                    largest=component
            alpha=bytearray(image.getchannel('A').tobytes())
            keep=bytearray(len(alpha))
            for k in largest:
                keep[k]=alpha[k]
            image.putalpha(Image.frombytes('L',(w,h),bytes(keep)))
        bounds=image.getchannel('A').point(lambda a:255 if a>35 else 0).getbbox()
        if bounds:
            image=image.crop(bounds)
        if upper_only:
            image=image.crop((0,0,image.width,round(image.height*.68)))
        data=image.tobytes('raw','RGBA')
        q=QImage(data,image.width,image.height,image.width*4,QImage.Format.Format_RGBA8888).copy()
        return QPixmap.fromImage(q)

def layer(p,pix,x,y,w,h):
    p.drawPixmap(QRectF(x,y,w,h),pix,QRectF(pix.rect()))

def pivot_layer(p,pix,x,y,w,h,angle,anchor=.5):
    p.save()
    p.translate(x,y)
    p.rotate(angle)
    layer(p,pix,-w*anchor,0,w,h)
    p.restore()

class WhaleRenderer:
    def __init__(self):
        path=HERE/'parts.png'
        boxes=[(0,0,397,447),(397,0,724,447),(724,0,1086,447),(1086,0,1448,447),
               (0,447,362,735),(362,447,724,735),(724,447,1086,735),(1086,447,1448,735),
               (0,735,340,1086),(360,735,645,1086),(650,735,1060,1086),(1060,735,1448,1086)]
        self.parts=[load_part(path,b,i in (4,6),i in (0,10,11)) for i,b in enumerate(boxes)]
        self.parts[1]=load_part(HERE/'back_hair.png')
        self.hungry=load_part(HERE/'hungry.png')
        self.eating=load_part(HERE/'states.png',(362,362,724,724))

    def draw(self,p,cx,foot,scale,pose,mode,t):
        p.save()
        p.translate(cx,foot)
        p.scale(scale,scale)
        if mode in ('hungry','eating'):
            pix=self.hungry if mode=='hungry' else self.eating
            h=228 if mode=='hungry' else 236
            w=h*pix.width()/pix.height()
            layer(p,pix,-w/2,-h,w,h)
            p.restore()
            return
        la,lf,ra,rf,lean,sway,stride,reach=pose
        p.translate(sway,0)
        # Each body segment keeps its pixel size; rotations are joint movement.
        p.translate(0,-105)
        p.rotate(lean)
        p.translate(0,105)
        p.save()
        p.translate(37,-72)
        p.rotate(-13+2*math.sin(t*2))
        layer(p,self.parts[3],0,-20,111,70)
        p.restore()
        layer(p,self.parts[1],-76,-220,152,185)
        pivot_layer(p,self.parts[8],-14,-43,25,44,stride)
        pivot_layer(p,self.parts[9],14,-43,25,44,-stride)
        layer(p,self.parts[2],-54,-131,108,100)
        elbows=[]
        for side,upper,lower,a,b in ((-1,4,5,la,lf),(1,6,7,ra,rf)):
            sx,sy=side*33,-122
            length=37*reach
            pivot_layer(p,self.parts[upper],sx,sy,24,length+5,-a)
            ex=sx+length*math.sin(math.radians(a))
            ey=sy+length*math.cos(math.radians(a))
            elbows.append((lower,ex,ey,b))
        head=11 if mode=='cool' else (10 if (t%9)<.32 else 0)
        p.save()
        p.translate(-8,-133)
        # Compensate for the tilt painted into the original head sprite.
        p.rotate(22)
        layer(p,self.parts[head],-78,-105,156,139)
        p.restore()
        for lower,ex,ey,b in elbows:
            pivot_layer(p,self.parts[lower],ex,ey-2,23,37*reach+5,-b)
        p.restore()

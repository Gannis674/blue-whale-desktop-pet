"""Turnaround artwork with two joint legs and planted-foot walking."""
import math
from PySide6.QtCore import QRectF
from .render import HERE,load_part,layer
from .patrol import foot_target

class WalkingRenderer:
    def __init__(self):
        path=HERE/'turnaround.png'
        # Source box, sole centre and skirt hem, measured in the authored atlas.
        specs=[((20,8,532,519),(236,515),450),
               ((540,8,996,519),(807,515),448),
               ((1042,12,1510,520),(1365,513),447),
               ((20,525,520,1005),(350,995),928),
               ((538,525,1009,1005),(802,995),927)]
        self.views=[]
        # Preserve atlas coordinates instead of trimming different views differently.
        from PIL import Image
        from PySide6.QtGui import QImage,QPixmap
        with Image.open(path) as im:
            for box,anchor,hem in specs:
                crop=im.crop(box).convert('RGBA')
                data=crop.tobytes()
                pix=QPixmap.fromImage(QImage(data,crop.width,crop.height,crop.width*4,QImage.Format.Format_RGBA8888).copy())
                ax,ay=anchor[0]-box[0],anchor[1]-box[1]
                scale=236./ay
                self.views.append((pix,ax,ay,hem-box[1],scale))
        leg=load_part(path,(1175,566,1482,973))
        w,h=leg.width(),leg.height()
        self.thigh=leg.copy(0,0,w,round(h*.36))
        self.shin=leg.copy(0,round(h*.30),w,round(h*.36))
        self.shoe=leg.copy(0,round(h*.64),w,h-round(h*.64))

    def bone(self,p,pix,a,b,width):
        dx,dy=b[0]-a[0],b[1]-a[1]
        p.save()
        p.translate(*a)
        p.rotate(-math.degrees(math.atan2(dx,dy)))
        layer(p,pix,-width/2,-1,width,math.hypot(dx,dy)+2)
        p.restore()

    def leg(self,p,cycle,offset,hipx,far=False):
        fx,fy,toe=foot_target(cycle,offset)
        hip=(hipx,-33.)
        ankle=(fx-2,fy-8.)
        dx,dy=ankle[0]-hip[0],ankle[1]-hip[1]
        distance=max(.001,math.hypot(dx,dy))
        # Equal 14-unit thigh and shin; knee bends forward, never sideways.
        bend=math.sqrt(max(0,14.**2-(distance/2)**2))
        knee=((hip[0]+ankle[0])/2+dy/distance*bend,
              (hip[1]+ankle[1])/2-dx/distance*bend)
        self.bone(p,self.thigh,hip,knee,16.)
        self.bone(p,self.shin,knee,ankle,15.)
        p.save()
        p.translate(fx,fy-4.5)
        p.rotate(toe)
        layer(p,self.shoe,-10,-8.5,23,13.)
        p.restore()

    def draw(self,p,cx,foot,scale,yaw,cycle,walking,blink=0.):
        angle=yaw%360.
        index=int((angle+22.5)//45)%8
        views=(0,1,2,3,4,3,2,1)
        view=views[index]
        mirror=index>4
        pix,ax,ay,hem,unit=self.views[view]
        p.save()
        p.translate(cx,foot)
        p.scale(scale*(-1 if mirror else 1),scale)
        # Small perspective change between authored 45-degree views; no zoom/fade.
        delta=(angle-index*45+180)%360-180
        p.scale(math.cos(math.radians(delta)),1.)
        if walking and view==2:
            self.leg(p,cycle,.5,-2.,True)
            self.leg(p,cycle,0.,2.)
            p.drawPixmap(QRectF(-ax*unit,-ay*unit,pix.width()*unit,hem*unit),
                         pix,QRectF(0,0,pix.width(),hem))
        else:
            layer(p,pix,-ax*unit,-ay*unit,pix.width()*unit,pix.height()*unit)
        if view==0 and blink>.01:
            self.eyelids(p,ax,ay,unit,blink)
        p.restore()

    def eyelids(self,p,ax,ay,unit,closure):
        from PySide6.QtGui import QColor,QPen,QPainterPath
        from PySide6.QtCore import Qt
        p.save()
        p.translate(-ax*unit,-ay*unit)
        p.scale(unit,unit)
        # Eye coordinates in the front atlas cell; eyelids are animated by the renderer.
        for x,y in ((180,207),(254,205)):
            eye=QRectF(x-23,y-19,46,38)
            mask=QPainterPath();mask.addEllipse(eye)
            p.save();p.setClipPath(mask)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor('#ffe2d2'))
            p.drawRect(QRectF(x-24,y-20,48,40*closure))
            p.restore()
            if closure>.85:
                p.setPen(QPen(QColor('#3b2634'),2.6,Qt.PenStyle.SolidLine,Qt.PenCapStyle.RoundCap))
                p.setBrush(Qt.BrushStyle.NoBrush)
                path=QPainterPath();path.moveTo(x-18,y+3)
                path.quadTo(x,y+13,x+18,y+3)
                p.drawPath(path)
        p.restore()

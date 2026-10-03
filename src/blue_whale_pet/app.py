"""Desktop whale: walking, feeding and pointer-hover greetings."""
import ctypes
from ctypes import wintypes
import math
import sys
import time
from PySide6.QtCore import Qt,QTimer,QPoint,QRectF
from PySide6.QtGui import QPainter,QColor,QFont,QGuiApplication,QImage,QCursor
from PySide6.QtWidgets import QApplication,QWidget,QMenu
from .logic import PetMood,REST,lane_bounds
from .render import WhaleRenderer
from .walk_render import WalkingRenderer
from .patrol import Patrol
from .hover import HoverGreeting,GREETING

class LastInput(ctypes.Structure):
    _fields_=[('cbSize',wintypes.UINT),('dwTime',wintypes.DWORD)]

def idle_seconds():
    record=LastInput(ctypes.sizeof(LastInput),0)
    if not ctypes.windll.user32.GetLastInputInfo(ctypes.byref(record)):return 0.
    ctypes.windll.kernel32.GetTickCount.restype=wintypes.DWORD
    return ((ctypes.windll.kernel32.GetTickCount()-record.dwTime)&0xffffffff)/1000

class PetWindow(QWidget):
    def __init__(self,controller):
        super().__init__()
        self.c=controller
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint|Qt.WindowType.Tool|Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setWindowTitle('蓝色大肥鱼 v4.3.1 · 高清陪伴')
        self.press=None
        self.dragged=False
        self.hit_image=None
        self.resize_for_pet()

    def resize_for_pet(self):
        self.dpr=self.c.dpr
        self.art_scale=self.c.size/236/self.dpr
        self.setFixedSize(math.ceil(max(236,self.c.size*1.65+20)/self.dpr),
                          math.ceil((self.c.size+70)/self.dpr))
        self.hit_image=None

    def render_pet(self):
        # Render at physical screen resolution. A logical-size bitmap gets
        # enlarged by Windows on a high-DPI display and blurs every outline.
        im=QImage(math.ceil(self.width()*self.dpr),math.ceil(self.height()*self.dpr),
                  QImage.Format.Format_ARGB32_Premultiplied)
        im.setDevicePixelRatio(self.dpr)
        im.fill(Qt.GlobalColor.transparent)
        p=QPainter(im)
        p.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        if self.c.mood.state=='calm':
            hover=self.c.hover
            yaw=hover.yaw if hover.blocking else self.c.patrol.yaw
            self.c.walk_renderer.draw(p,self.width()/2,self.height()-5/self.dpr,
                self.art_scale,yaw,self.c.patrol.cycle,
                self.c.is_walking and self.c.patrol.state=='walk',hover.blink())
        else:
            self.c.whale_renderer.draw(p,self.width()/2,self.height()-5/self.dpr,
                self.art_scale,self.c.pose,self.c.mood.state,self.c.now)
        p.end()
        self.hit_image=im
        return im

    def pet_contains(self,global_pos):
        local=self.mapFromGlobal(global_pos)
        if self.hit_image is None:self.render_pet()
        ratio=self.hit_image.devicePixelRatio()
        pixel=QPoint(math.floor(local.x()*ratio),math.floor(local.y()*ratio))
        return (self.hit_image.rect().contains(pixel)
                and self.hit_image.pixelColor(pixel).alpha()>40)

    def paintEvent(self,_event):
        im=self.render_pet()
        p=QPainter(self)
        p.setRenderHints(QPainter.RenderHint.Antialiasing|QPainter.RenderHint.SmoothPixmapTransform)
        p.drawImage(0,0,im)
        message=self.c.display_bubble()
        if message:
            rect=QRectF(2/self.dpr,3/self.dpr,self.width()-4/self.dpr,53/self.dpr)
            p.setBrush(QColor('#f5f8ff'));p.setPen(QColor('#527bb4'))
            p.drawRoundedRect(rect,8/self.dpr,8/self.dpr)
            font=QFont('Microsoft YaHei UI')
            font.setPixelSize(max(6,round(14/self.dpr)))
            p.setFont(font);p.setPen(QColor('#183a61'))
            p.drawText(rect.adjusted(5/self.dpr,0,-5/self.dpr,0),Qt.AlignmentFlag.AlignCenter,message)
        p.end()

    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.press=(event.globalPosition(),self.c.x)
            self.dragged=False;self.c.dragging=True

    def mouseMoveEvent(self,event):
        if self.press:
            delta=event.globalPosition()-self.press[0]
            if abs(delta.x())+abs(delta.y())>3:self.dragged=True
            if self.dragged:
                self.c.x=max(self.c.lo,min(self.press[1]+delta.x(),self.c.hi))
                self.move(round(self.c.x),round(self.c.y))

    def mouseReleaseEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:
            self.c.dragging=False
            if self.press and not self.dragged:self.c.feed()
            self.press=None

    def contextMenuEvent(self,event):self.c.show_menu(event.globalPos())
    def keyPressEvent(self,event):
        if event.key()==Qt.Key.Key_Escape:QApplication.quit()

class DesktopPet:
    def __init__(self,idle_reader=idle_seconds,clock=time.monotonic,screen=None,cursor_reader=QCursor.pos):
        self.clock=clock
        self.screen=screen or QGuiApplication.primaryScreen()
        self.dpr=self.screen.devicePixelRatio()
        self.size=150
        self.idle_reader=idle_reader
        self.cursor_reader=cursor_reader
        self.mood=PetMood()
        self.now=self.last_tick=self.clock()
        self.last_idle_check=0.
        self.idle=0.
        self.pose=REST
        self.patrol=Patrol()
        self.hover=HoverGreeting()
        self.hover_anchor=None
        self.hover_miss=0.
        self.is_walking=False
        self.auto_walk=True
        self.dragging=False
        self.menu_open=False
        self.bubble=''
        self.bubble_until=0.
        self.whale_renderer=WhaleRenderer()
        self.walk_renderer=WalkingRenderer()
        self.whale=PetWindow(self)
        self.refresh_lane()
        self.x,self.y=self.lo,self.lane_y
        self.whale.move(round(self.x),round(self.y))
        self.whale.show()
        self.timer=QTimer()
        self.timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.timer.timeout.connect(self.tick)
        self.timer.start(16)

    def refresh_lane(self):
        r=self.screen.availableGeometry()
        self.lo,self.hi,self.lane_y=lane_bounds(r.x(),r.y(),r.width(),r.height(),
            self.whale.width(),self.whale.height(),self.dpr)

    def display_bubble(self):
        if self.hover.active and self.hover.age>=.35:return GREETING
        if self.bubble and (self.bubble_until is None or self.now<self.bubble_until):return self.bubble
        return ''

    def changed(self):
        self.hover.reset(self.patrol.yaw)
        self.hover_anchor=None
        self.bubble=''
        if self.mood.state=='hungry':
            self.bubble='呜…碗都空了。\n可以给我一点白米饭吗？'
            self.bubble_until=None
        elif self.mood.state=='eating':
            self.bubble='啊呜！收到一口 token。';self.bubble_until=self.now+1.2
        elif self.mood.state=='cool':
            self.bubble='本鱼现在很有实力。';self.bubble_until=self.now+3

    def feed(self):
        self.now=self.clock();self.mood.feed(self.now);self.changed()

    def request_food(self):
        self.now=self.clock();self.mood.request_food(self.now);self.changed()

    def update_hover(self,dt):
        if self.mood.state!='calm' or self.dragging or self.menu_open:
            self.hover.reset(self.patrol.yaw);self.hover_anchor=None;self.hover_miss=0.
            return
        pos=self.cursor_reader()
        inside=self.whale.pet_contains(pos)
        # Turning changes the silhouette under a stationary cursor. Keep that
        # encounter until the pointer moves away, so the greeting never flickers.
        if self.hover.active and self.hover_anchor is not None:
            inside=inside or (pos-self.hover_anchor).manhattanLength()<=2
        if inside:
            self.hover_miss=0.
            if not self.hover.active:self.hover_anchor=QPoint(pos)
        else:
            self.hover_miss+=dt
            if self.hover.active and self.hover_miss<.15:inside=True
        self.hover.step(inside,dt,self.patrol.yaw)
        if not self.hover.blocking:self.hover_anchor=None

    def tick(self):
        self.now=self.clock()
        dt=max(0.,min(self.now-self.last_tick,.05))
        self.last_tick=self.now
        if self.now-self.last_idle_check>=.25:
            self.idle=self.idle_reader();self.last_idle_check=self.now
        if self.mood.advance(self.now,self.idle):self.changed()
        self.update_hover(dt)
        self.is_walking=False
        target=(-48,110,48,-110,0,0,0,1) if self.mood.state=='cool' else REST
        alpha=1-math.exp(-20*dt)
        self.pose=tuple(a+(b-a)*alpha for a,b in zip(self.pose,target))
        self.refresh_lane()
        if self.mood.state=='calm' and self.auto_walk and not self.dragging and not self.menu_open and not self.hover.blocking:
            self.is_walking=True
            self.x=self.patrol.step(self.x,self.lo,self.hi,dt,26/self.dpr,self.size/236/self.dpr)
        self.x=max(self.lo,min(self.x,self.hi));self.y=self.lane_y
        self.whale.move(round(self.x),round(self.y));self.whale.update()

    def set_size(self,size):
        self.size=size;self.whale.resize_for_pet();self.refresh_lane()
        self.x=max(self.lo,min(self.x,self.hi));self.y=self.lane_y

    def show_menu(self,point):
        self.menu_open=True
        menu=QMenu()
        menu.addAction('喂一口白米饭（token）',self.feed)
        menu.addAction('看看哭哭讨饭的样子',self.request_food)
        menu.addSeparator()
        walk=menu.addAction('持续散步');walk.setCheckable(True);walk.setChecked(self.auto_walk)
        walk.toggled.connect(lambda checked:setattr(self,'auto_walk',checked))
        sizes=menu.addMenu('大小')
        for title,size in (('小巧 · 120',120),('默认 · 150',150),('稍大 · 180',180)):
            sizes.addAction(title,lambda checked=False,value=size:self.set_size(value))
        menu.addSeparator();menu.addAction('退出',QApplication.quit)
        try:menu.exec(point)
        finally:self.menu_open=False;menu.deleteLater()

def main():
    if sys.platform!='win32':
        raise SystemExit('Blue Whale Desktop Pet requires Windows.')
    kernel=ctypes.windll.kernel32
    kernel.CreateMutexW.argtypes=[ctypes.c_void_p,wintypes.BOOL,wintypes.LPCWSTR]
    kernel.CreateMutexW.restype=wintypes.HANDLE
    handle=kernel.CreateMutexW(None,False,'Local\\BlueWhalePetV4')
    if kernel.GetLastError()==183:return
    app=QApplication(sys.argv);app.setQuitOnLastWindowClosed(False)
    controller=DesktopPet()
    try:app.exec()
    finally:
        kernel.CloseHandle.argtypes=[wintypes.HANDLE];kernel.CloseHandle(handle)

if __name__=='__main__':main()

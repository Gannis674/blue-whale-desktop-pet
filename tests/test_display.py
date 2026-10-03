import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import math
import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QRect,QPoint
from blue_whale_pet.app import DesktopPet
from blue_whale_pet.hover import GREETING

class Screen:
    def __init__(self,dpr):self.dpr=dpr
    def devicePixelRatio(self):return self.dpr
    def availableGeometry(self):return QRect(0,0,1440,960)

class DisplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])

    def test_native_resolution_and_hover_at_multiple_scalings(self):
        for dpr in (1.,1.25,1.5,2.):
            with self.subTest(dpr=dpr):
                clock=[100.];cursor=[QPoint(-500,-500)]
                pet=DesktopPet(screen=Screen(dpr),clock=lambda:clock[0],
                               idle_reader=lambda:0.,cursor_reader=lambda:cursor[0])
                pet.timer.stop()
                try:
                    im=pet.whale.render_pet()
                    self.assertEqual(im.width(),math.ceil(pet.whale.width()*dpr))
                    self.assertEqual(im.height(),math.ceil(pet.whale.height()*dpr))
                    self.assertEqual(im.devicePixelRatio(),dpr)
                    centre=QPoint(pet.whale.width()//2,pet.whale.height()-round(50/dpr))
                    solid=[QPoint(x,y) for y in range(pet.whale.height()) for x in range(pet.whale.width())
                           if pet.whale.pet_contains(pet.whale.mapToGlobal(QPoint(x,y)))]
                    point=min(solid,key=lambda p:(p-centre).manhattanLength())
                    cursor[0]=pet.whale.mapToGlobal(point);before=pet.x
                    for _ in range(60):clock[0]+=1/60;pet.tick();self.app.processEvents()
                    self.assertTrue(pet.hover.active)
                    self.assertEqual(pet.x,before)
                    self.assertEqual(pet.display_bubble(),GREETING)
                    cursor[0]=QPoint(-500,-500)
                    for _ in range(60):clock[0]+=1/60;pet.tick();self.app.processEvents()
                    self.assertFalse(pet.hover.blocking)
                    self.assertGreater(pet.x,before)
                finally:pet.whale.close()

if __name__=='__main__':unittest.main()

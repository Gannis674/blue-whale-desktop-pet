import math
import unittest
from blue_whale_pet.logic import PetMood,lane_bounds
from blue_whale_pet.patrol import Patrol,foot_target
from blue_whale_pet.hover import HoverGreeting

class BehaviorTests(unittest.TestCase):
    def test_planted_feet_do_not_slide(self):
        for cycle in (.02,.15,.35,.55):
            x,y,_=foot_target(cycle)
            next_x,next_y,_=foot_target(cycle+.001)
            self.assertAlmostEqual(x,next_x+.04)
            self.assertEqual((y,next_y),(0.,0.))
        self.assertLess(foot_target(.8)[1],-6.9)
        for i in range(100):
            self.assertEqual(max(foot_target(i/100)[1],foot_target(i/100,.5)[1]),0.)

    def test_five_round_trips_then_one_full_spin(self):
        patrol=Patrol();x=0.;spins=[];last='walk';start=0.
        for _ in range(18000):
            old_x=x;x=patrol.step(x,0,100,1/60,26,150/236)
            self.assertTrue(0<=x<=100)
            if patrol.state=='spin':
                self.assertEqual(x,old_x)
                if last!='spin':spins.append(patrol.legs);start=patrol.start_yaw
            elif last=='spin':self.assertAlmostEqual(patrol.yaw-start,360)
            if patrol.state=='walk':
                self.assertEqual(round(patrol.yaw%360),90 if patrol.direction>0 else 270)
            last=patrol.state
            if len(spins)==2 and last=='walk':break
        self.assertEqual(spins,[10,20])

    def test_hover_faces_front_blinks_and_returns(self):
        for heading in (90,270,810):
            hover=HoverGreeting();blinks=[]
            for _ in range(90):hover.step(True,1/60,heading);blinks.append(hover.blink())
            self.assertTrue(hover.active)
            self.assertAlmostEqual(hover.yaw%360,0)
            self.assertGreater(max(blinks),.97)
            for _ in range(30):hover.step(False,1/60,heading)
            self.assertFalse(hover.blocking)
            self.assertAlmostEqual(hover.yaw%360,heading%360)

    def test_hunger_and_fifteen_second_sunglasses(self):
        mood=PetMood();mood.advance(599,599);self.assertEqual(mood.state,'calm')
        mood.advance(600,600);self.assertEqual(mood.state,'hungry')
        mood.advance(1800,1800);self.assertEqual(mood.state,'hungry')
        mood.feed(2000);mood.advance(2001.2,0);self.assertEqual(mood.state,'cool')
        mood.advance(2016.19,0);self.assertEqual(mood.state,'cool')
        mood.advance(2016.2,0);self.assertEqual(mood.state,'calm')

    def test_window_remains_in_lane(self):
        lo,hi,y=lane_bounds(0,0,1440,960,134,110,2)
        self.assertGreaterEqual(lo,1440*.78)
        self.assertLessEqual(hi+134,1440)
        self.assertLessEqual(y+110,960)

if __name__=='__main__':unittest.main()

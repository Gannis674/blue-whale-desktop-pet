"""A reversible hover greeting that pauses the existing patrol."""
from dataclasses import dataclass
import math
from .patrol import ease

GREETING='好棒主人，\n我们一起又中了一篇SCI。'

@dataclass
class HoverGreeting:
    active:bool=False
    returning:bool=False
    age:float=0.
    elapsed:float=0.
    yaw:float=90.
    start:float=90.
    target:float=0.

    @property
    def blocking(self):
        return self.active or self.returning

    def reset(self,yaw):
        self.active=self.returning=False
        self.age=self.elapsed=0.
        self.yaw=yaw

    def step(self,inside,dt,patrol_yaw):
        if inside and not self.active:
            self.start=self.yaw if self.returning else patrol_yaw
            self.target=self.start+(0-self.start+180)%360-180
            self.elapsed=self.age=0.
            self.active,self.returning=True,False
        elif not inside and self.active:
            self.start=self.yaw
            self.target=self.start+(patrol_yaw-self.start+180)%360-180
            self.elapsed=0.
            self.active,self.returning=False,True
        if self.blocking:
            self.elapsed+=dt
            self.yaw=self.start+(self.target-self.start)*ease(self.elapsed/.35)
            if self.active:
                self.age+=dt
            elif self.elapsed>=.35:
                self.returning=False
        else:
            self.yaw=patrol_yaw

    def blink(self):
        if not self.active:return 0.
        t=self.age%4.5
        for start in (.52,.92):
            u=(t-start)/.24
            if 0<=u<=1:return math.sin(math.pi*u)**2
        return 0.

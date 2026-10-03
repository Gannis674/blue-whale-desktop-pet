"""Distance-driven steps, endpoint turns, and a spin after five round trips."""
from dataclasses import dataclass
import math

def ease(t):
    t=max(0.,min(1.,t))
    return t*t*(3-2*t)

def foot_target(cycle,offset=0.):
    u=(cycle+offset)%1.
    if u<.6:
        # The planted foot travels backwards relative to the moving hip.
        # One complete cycle advances the character 40 model units.
        return 12.-40.*u,0.,0.
    swing=(u-.6)/.4
    return -12.+24.*ease(swing),-7.*math.sin(math.pi*swing)**2,math.sin(2*math.pi*swing)*5.

@dataclass
class Patrol:
    direction:int=1
    yaw:float=90.
    cycle:float=0.
    legs:int=0
    spins:int=0
    state:str='walk'
    elapsed:float=0.
    start_yaw:float=90.
    spin_pending:bool=False

    def step(self,x,lo,hi,dt,speed,model_scale):
        if hi-lo<1e-6:
            return lo
        if self.state!='walk':
            self.elapsed+=dt
            duration=.44 if self.state=='turn' else 1.8
            angle=180. if self.state=='turn' else 360.
            self.yaw=self.start_yaw+angle*ease(self.elapsed/duration)
            if self.elapsed>=duration:
                self.yaw=self.start_yaw+angle
                if self.state=='turn' and self.spin_pending:
                    self.state='spin'
                    self.start_yaw=self.yaw
                    self.elapsed=0.
                    self.spin_pending=False
                    self.spins+=1
                else:
                    self.state='walk'
                    self.cycle=0.
            return x
        nx=max(lo,min(hi,x+self.direction*speed*dt))
        self.cycle=(self.cycle+abs(nx-x)/max(model_scale*40.,.001))%1.
        if (self.direction>0 and nx>=hi) or (self.direction<0 and nx<=lo):
            self.legs+=1
            self.direction*=-1
            self.start_yaw=self.yaw
            self.elapsed=0.
            self.state='turn'
            self.spin_pending=self.legs%10==0
        return nx

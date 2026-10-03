"""Feeding and idle hunger; no additional idle-time characters."""
from dataclasses import dataclass
REST=(-5.,-8.,5.,8.,0.,0.,0.,1.)

def lane_bounds(left,top,width,height,ww,wh,dpr=1.):
    right,bottom=left+width,top+height
    lane_right=right-18/dpr-ww
    lane_left=max(left+4/dpr,min(max(left+width*.78,right-540/dpr),lane_right))
    return lane_left,lane_right,bottom-wh-4/dpr

@dataclass
class PetMood:
    state:str='calm'
    last_fed:float=float('-inf')
    started:float=0.
    until:float=0.

    def advance(self,now,idle):
        previous=self.state
        if self.state=='eating' and now>=self.until:
            self.state,self.started,self.until='cool',now,now+15
        elif self.state=='cool' and now>=self.until:self.state='calm'
        if self.state=='calm' and min(idle,now-self.last_fed)>=600:self.state='hungry'
        return previous!=self.state

    def feed(self,now):
        self.state,self.started,self.until,self.last_fed='eating',now,now+1.2,now

    def request_food(self,now):self.state,self.started='hungry',now

from em_lib2wd import WR2WD_emulator
import math

# https://qiita.com/noca/items/f7ffd4acc641a809ac67
# https://qiita.com/noca/items/a132bb5e1ad4bf4eff6a
# https://github.com/pytransitions/transitions
from transitions import Machine

from WDT import WatchDogTimer

class robot:
    def __init__(self, wr):
        self.wr = wr

        states = ['READY', 'FORWARD', 'TURN_LEFT', 'INSIDE', 'OUTSIDE']
        T='trigger'; S='source'; D='dest'; A='after'; B='before'; C='conditions';
        transitions = [
            { T: 't_bottom_black',    S: 'READY',     D: 'FORWARD',    A: 'state_action' },
            { T: 't_bottom_white',    S: 'FORWARD',   D: 'TURN_LEFT',  A: 'state_action' },
            { T: 't_timer_turn_left', S: 'TURN_LEFT', D: 'OUTSIDE',    A: 'state_action' },
            { T: 't_bottom_black',     S: 'OUTSIDE',  D: 'INSIDE',     A: 'state_action' },
            { T: 't_bottom_white',     S: 'INSIDE',   D: 'OUTSIDE',    A: 'state_action' },
        ]
        self.machine = Machine(model=self,
                               initial='READY',
                               states=states,
                               transitions=transitions,
                               auto_transitions=False,
                               ignore_invalid_triggers=True)

        self.state_func_led = {
            'READY':     self.wr.led.white,
            'FORWARD':   self.wr.led.magenta,
            'TURN_LEFT': self.wr.led.green,
            'INSIDE':    self.wr.led.blue,
            'OUTSIDE':   self.wr.led.red,
            }
        self.state_func_led_else = self.wr.led.black

        self.state_func_mc = {
            'READY':     self.wr.mc.stop,
            'FORWARD':   self.wr.mc.front,
            'TURN_LEFT': self.wr.mc.turn_left,
            'INSIDE':    self.wr.mc.front_tr,
            'OUTSIDE':   self.wr.mc.front_tl,
            }
        self.state_func_mc_else = self.wr.led.black


    def state_led(self):
        if( self.state in self.state_func_led.keys() ):
            self.state_func_led[self.state]()
        else:
            self.state_func_led_else()

    def state_mc(self):
        if( self.state in self.state_func_mc.keys() ):
            self.state_func_mc[self.state]()
        else:
            self.state_func_mc_else()

    def state_action(self):
        self.state_mc()
        self.state_led()
        if( self.state == 'TURN_LEFT' ):
            print(self.t_timer_turn_left)
            self.wdt = WatchDogTimer( 1.0, self.t_timer_turn_left )
            self.wdt.start()

    def loop(self):
        if( self.wr.ps.bottom() ): # white
            self.t_bottom_white()
        else: # black
            self.t_bottom_black()


def field( x, y ): # True for white, False for black
    return x*x+y*y > 1000*1000
#   return math.fabs(x) > 1000 or math.fabs(y) > 1000

def main():
    wr = WR2WD_emulator(field = field)
    rb = robot(wr)

    while( True ):
        try:
            rb.loop()

        except KeyboardInterrupt:
            print( '\nbye')
            break

if( __name__ == '__main__' ):
    main()

import math
import time
from threading import Thread

class Field:
    @classmethod
    def __prefix(cls):
        return 'field_'

    @classmethod
    def available_names(cls):
        prefix = cls.__prefix()
        networks = []
        for name in dir(cls):
            if( name.startswith(prefix ) ):
                networks.append( name[len(prefix):] )
        return networks

    def __init__( self, name ):
        if( not ( name in self.available_names() ) ):
            raise NotImplementedError( '**' + name + '** is not implemented.')

        self.func = eval(self.__class__.__name__+'.'+self.__prefix()+name)

    def __call__( self, x, y ):
        return self.func( x, y )

    '''
        True:  WHITE
        False: BLACK
    '''

    @classmethod
    def field_black_circle( cls, x, y ):
        return x*x+y*y>1000*1000

    @classmethod
    def field_black_box( cls, x, y ):
        return math.fabs( x ) > 1000 or math.fabs( y ) > 1000

    @classmethod
    def field_white( cls, x, y ):
        return True

    @classmethod
    def field_black( cls, x, y ):
        return False

    @classmethod
    def field_black_white( cls, x, y ):
        return x > 0

    @classmethod
    def field_white_black( cls, x, y ):
        return x <= 0


class LED:
    def __init__(self, rb):
        self.rb = rb

    def write(self, R, G, B ):
        self.rb.state['LED'] = [R,G,B]
#       print( '** LED:', R, G, B )

    def off(self):
        self.write(0, 0, 0)

    def on(self):
        self.write(1, 1, 1)

    def red(self):
        self.write(1, 0, 0)

    def green(self):
        self.write(0, 1, 0)

    def blue(self):
        self.write(0, 0, 1)

    def cyan(self):
        self.write(0, 1, 1)

    def magenta(self):
        self.write(1, 0, 1)

    def yellow(self):
        self.write(1, 1, 0)

    def white(self):
        self.write(1, 1, 1)

    def black(self):
        self.write(0, 0, 0)

class MotorControl():
    def __init__( self, rb ):
        self.str_lr = ['LEFT ', 'RIGHT']
        self.rb = rb
        self.duty = 100

    def posneg( self, p0, p1 ):
        ret = 0
        if( p0 == 1 and p1 == 0 ):
            ret = +1
        elif( p0 == 0 and p1 == 1 ):
            ret = -1
        return ret

    def write( self, lr, p0, p1 ):
        v = self.duty * self.posneg( p0, p1 )
        self.rb.state['VEL'][lr] = v
#       print( '** ', self.str_lr[lr], v )

    def left_write( self, p0, p1 ):
        self.write( 0, p0, p1 )

    def right_write( self, p0, p1 ):
        self.write( 1, p0, p1 )

    def stop(self):
        self.left_write(0, 0)
        self.right_write(0, 0)

    def front(self):
        self.left_write(1, 0)
        self.right_write(1, 0)

    def front_tl(self):
        self.left_write(0, 0)
        self.right_write(1, 0)

    def front_tr(self):
        self.left_write(1, 0)
        self.right_write(0, 0)

    def back(self):
        self.left_write(0, 1)
        self.right_write(0, 1)

    def back_tl(self):
        self.left_write(0, 0)
        self.right_write(0, 1)

    def back_tr(self):
        self.left_write(0, 1)
        self.right_write(0, 0)

    def turn_left(self):
        self.left_write(0, 1)
        self.right_write(1, 0)

    def turn_right(self):
        self.left_write(1, 0)
        self.right_write(0, 1)

    def brake(self):
        self.left_write(1, 1)
        self.right_write(1, 1)

    def speed(self, value):
        if value is not None:
            if value < 0.0:
                value = 0.0
            if value > 100.0:
                value = 100.0
            self.duty = value

class PhotoSensor:
    def __init__(self,rb, field, depth):
        self.rb = rb
        self.field = field
        self.depth = depth

    def front(self):
        raise NotImplementedError()

    def left(self):
        raise NotImplementedError()

    def right(self):
        raise NotImplementedError()

    def bottom(self): # white: True, black: False
        L = self.depth/2
        x = self.rb.state['POS'][0]
        y = self.rb.state['POS'][1]
        rad = self.rb.state['POS'][2]

        x += L * math.cos(rad)
        y += L * math.sin(rad)
        res = self.field( x, y )

#       print( '** BOTTOM', res )
        return res


class WR2WD_emulator(Thread):
    '''
    https://prod.kyohritsu.com/KP-RSPY2WD.html#manual
    Specifications

    Max velocity: 130 mm/s
    Size: 147(W)×105(D)×44(H) mm
    '''

    MAX_VEL = 130
    WIDTH = 147
    DEPTH = 105

    def __init__( self, fps=5, disp_frame=5, field = Field('black_white') ):
        Thread.__init__(self)
        self.daemon = True

        self.T = 1/fps
        self.disp_frame = disp_frame

        self.state = { 'LED': [0,0,0],# R G B
                       'POS': [0,0, math.pi/2],  # x, y, rad
                       'VEL': [0,0],  # left, right
                       }

        self.led = LED(self)
        self.mc = MotorControl(self)
        self.ps = PhotoSensor(self, field, self.DEPTH)

        self.running = True
        Thread.start(self)

    def __del__( self ):
        self.stop()

    def stop( self ):
        self.running = False
        self.join()

    def run( self ):
            self.frame = 1
            while( self.running ):
                time.sleep(self.T)
                self.update()
                self.frame += 1
                if( self.frame >= self.disp_frame ):
                    self.disp_state()
                    self.frame = 0

    def disp_state( self ):
        pos = self.state['POS']
        vel = self.state['VEL']
        led = self.state['LED']
        rad = pos[2] * 180 / math.pi
        while( rad < 0 ):
            rad += 360
        while( rad >= 360 ):
            rad -= 360

        r = math.sqrt(pos[0]*pos[0]+pos[1]*pos[1])
        t = math.atan2( pos[1], pos[0] ) *180/math.pi
        while( t < 0 ):
            t += 360
        while( t >= 360 ):
            t -= 360
        print( '+---------------------' )
        print( '| POS {:7.0f} {:7.0f} {:7.3f}'.format( pos[0], pos[1], rad ) )
        print( '| R+T {:7.0f} {:7.3f}'.format( r, t ) )
        print( '| LED ', led[0], led[1], led[2], '  VEL', vel[0], vel[1] )

    def update( self ):
        Vleft  = self.state['VEL'][0] / 100 * self.MAX_VEL
        Vright = self.state['VEL'][1] / 100 * self.MAX_VEL

        if( Vleft == Vright ): # forward or backward
            L = Vright * self.T
            rad = self.state['POS'][2]
            self.state['POS'][0] += L * math.cos( rad )
            self.state['POS'][1] += L * math.sin( rad )

        elif( Vleft == 0 and math.fabs(Vright) ): # right is on
            L = Vright * self.T
            dr = L / (self.WIDTH)

            x0 = self.state['POS'][0]
            y0 = self.state['POS'][1]
            r0 = self.state['POS'][2]

            r = r0 + 90 * (math.pi/180)
            cx = x0 + (self.WIDTH/2) * math.cos(r)
            cy = y0 + (self.WIDTH/2) * math.sin(r)

            r = r0 - 90 * (math.pi/180) + dr
            x1 = cx + (self.WIDTH/2) * math.cos(r)
            y1 = cy + (self.WIDTH/2) * math.sin(r)

            self.state['POS'][0] = x1
            self.state['POS'][1] = y1
            self.state['POS'][2] += dr

        elif( Vright == 0 and math.fabs(Vleft) ):# left is on
            L = Vleft * self.T
            dr = L / (self.WIDTH)

            x0 = self.state['POS'][0]
            y0 = self.state['POS'][1]
            r0 = self.state['POS'][2]

            r = r0 - 90 * (math.pi/180)
            cx = x0 + (self.WIDTH/2) * math.cos(r)
            cy = y0 + (self.WIDTH/2) * math.sin(r)


            r = r0 + 90 * (math.pi/180) - dr
            x1 = cx + (self.WIDTH/2) * math.cos(r)
            y1 = cy + (self.WIDTH/2) * math.sin(r)

            self.state['POS'][0] = x1
            self.state['POS'][1] = y1
            self.state['POS'][2] -= dr


        else: # turn left or right
            L = Vright * self.T
            rad = L / (self.WIDTH/2)
            self.state['POS'][2] += rad

if( __name__ == '__main__' ):
    wr = WR2WD_emulator()
    wr.stop()

    wr.mc.front()
    wr.update()
    wr.disp_state()

    wr.mc.back()
    wr.update()
    wr.disp_state()

    wr.mc.turn_left()
    wr.update()
    wr.disp_state()

    wr.mc.turn_right()
    wr.update()
    wr.disp_state()

    wr.mc.front_tl()
    wr.update()
    wr.disp_state()

    wr.mc.front_tr()
    wr.update()
    wr.disp_state()


    wr.disp_state()
    for i in range(3):
        wr.mc.front_tr()
        wr.update()
        wr.disp_state()


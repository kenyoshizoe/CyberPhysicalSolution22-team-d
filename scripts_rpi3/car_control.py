from enum import Enum, IntEnum
from raspythoncar.wr_lib2wd import WR2WD
import time


class State(IntEnum):
    WAIT_FOR_JUDGE = 1
    CATCHING_ANT = 2
    CATCHING_BEE = 3

    BEFORE_LINETRACE_WALL = 4
    BEFORE_LINETRACE_ANT_BEE_LINE = 5
    ANT_BEE_LINE_TO_CENTER_LINE = 6

    LINETRACE_WALL = 10
    LINETRACE_CENTER_LINE = 12
    LINETRACE_ANT_BEE_LINE = 13
    LINETRACE_STOP_CENTER = 14


class Target(Enum):
    ant = 0
    bee = 1


class Timer:
    def __init__(self):
        self.timer = time.time()

    def reset(self):
        self.timer = time.time()

    def get_time(self):
        return time.time() - self.timer


class Driver:
    def __init__(self, wr):
        self.state = State.WAIT_FOR_JUDGE
        self.wr = wr
        self.timer = Timer()
        self.target = Target.ant

    def update(self):
        if self.state == State.WAIT_FOR_JUDGE:
            self.wr.mc.stop()
        elif self.state == State.BEFORE_LINETRACE_WALL:
            # turn right/left 90
            if self.target == Target.ant:
                self.wr.mc.turn_right()
            else:
                self.wr.mc.turn_left()
            self.wr.led.red()
            time.sleep(0.8)

            # go straight
            self.wr.mc.front()
            self.wr.led.green()
            time.sleep(2.1)

            # turn left/right 90+
            if self.target == Target.ant:
                self.wr.mc.turn_left()
            else:
                self.wr.mc.turn_right()
            time.sleep(0.75)

            # go straight
            self.wr.mc.front()
            time.sleep(1.0)

            print("LINETRACE_WALL")
            self.timer.reset()
            self.state = State.LINETRACE_WALL

        elif self.state == State.BEFORE_LINETRACE_ANT_BEE_LINE:
            # turn left / rifht
            if self.target == Target.ant:
                self.wr.mc.right()
            else:
                self.wr.mc.left()
            sleep(0.3)
            # go stragiht by FF
            self.wr.mc.front()
            self.wr.led.green()
            while self.wr.ps.bottom() == True:
                pass
            self.wr.led.blue()
            time.sleep(0.8)

            # turn left/right
            if self.target == Target.ant:
                self.wr.mc.turn_left()
            else:
                self.wr.mc.turn_right()
            self.wr.led.green()
            time.sleep(0.9)

            print("LINETRACE_ANT_BEE_LINE")
            self.timer.reset()
            self.state = State.LINETRACE_ANT_BEE_LINE

        elif self.state == State.ANT_BEE_LINE_TO_CENTER_LINE:
            # push straight
            self.wr.mc.front()
            while not (self.wr.ps.left() if self.target == Target.ant else self.wr.ps.right()):
                pass
            # go back
            self.wr.mc.back()
            time.sleep(0.5)
            # turn to center line
            if self.target == Target.ant:
                self.wr.mc.turn_left()
            else:
                self.wr.mc.turn_right()
            self.wr.led.magenta()
            time.sleep(1.1)
            # go straight until center line
            self.wr.mc.front()
            while self.wr.ps.bottom():
                pass

            print("LINETRACE_CENTER_LINE")
            self.timer.reset()
            self.state = State.LINETRACE_CENTER_LINE

        elif self.state == State.LINETRACE_WALL
            self.wr.mc.front()
            if self.timer.get_time() > 3.0:
                print("BEFORE_LINETRACE_ANT_BEE_LINE")
                self.timer.reset()
                self.state = State.BEFORE_LINETRACE_ANT_BEE_LINE
                return
        else:
            sensor_val = False
            elif self.state == State.LINETRACE_ANT_BEE_LINE:
                sensor_val = self.wr.ps.bottom()
                if  self.target == Target.ant:
                    sensor_val = not sensor_val
                if self.timer.get_time() > 4.0:
                    print("ANT_BEE_LINE_TO_CENTER_LINE")
                    self.timer.reset()
                    self.state = State.ANT_BEE_LINE_TO_CENTER_LINE
                    return
            elif self.state == State.LINETRACE_CENTER_LINE:
                sensor_val = self.wr.ps.bottom()
                if self.timer.get_time() > 2.0 and not self.wr.ps.right() and not self.wr.ps.left():
                    print("LINETRACE_STOP_CENTER")
                    self.timer.reset()
                    self.state = State.LINETRACE_STOP_CENTER
                    return
            elif self.state == State.LINETRACE_STOP_CENTER:
                sensor_val = self.wr.ps.bottom()
                if self.timer.get_time() > 2.5:
                    print("WAIT_FOR_JUDGE")
                    self.timer.reset()
                    self.state = State.WAIT_FOR_JUDGE
                    self.wr.mc.stop()
                    return

            if (sensor_val):
                self.wr.mc.front_tr()
                self.wr.led.red()
            else:
                self.wr.mc.front_tl()
                self.wr.led.blue()

    def ant(self):
        if self.state == State.WAIT_FOR_JUDGE:
            print("start catching ant")
            self.target = Target.ant
            self.timer.reset()
            self.state = State.BEFORE_LINETRACE_WALL

    def bee(self):
        if self.state == State.WAIT_FOR_JUDGE:
            print("start catching bee")
            self.target = Target.bee
            self.timer.reset()
            self.state = State.BEFORE_LINETRACE_WALL

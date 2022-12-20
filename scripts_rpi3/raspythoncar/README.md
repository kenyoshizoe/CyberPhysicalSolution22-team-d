# [RasPython Car](https://prod.kyohritsu.com/KP-RSPY2WD.html)

## wr_lib2wd.py

Official API


### [RasPythonカー プログラミングカリキュラム](https://prod.kyohritsu.com/RASPYTHONCAR/tutorial_python/index.html)

### [wr_lib2wd 関数リファレンス](https://prod.kyohritsu.com/RASPYTHONCAR/functions/index.html)

## em_lib2wd.py

Very simple emulator by mtanaka@sc.e.titech.ac.jp

'''
from em_lib2wd import WR2WD_emulator

def field( x, y ): # True for white, False for black
    return x*x+y*y > 1000*1000

wr = WR2WD_emulator(func_white_black = field)
'''

### class WR2WD_emulator

- def **__init__** ( self, fps=5, disp_frame=5, func_white_black = lambda x, y: x>0 )

	*fps* is frame-per-second of update the machine status. 
	The status is displayed each *disp_frame* frames.

- led (LED)

	write, off, on, red, green, blue, cyan, magenta, yellow, white, black

- mc (MotorControl)

	stop, front, front_tl, front_tr, back, back_tl, back_tr, turn_left, turn_right, brake, speed

- ps (PhotoSensor)

	bottom

## sm_sample.py

A sample of a state machine using the emulator of a RasPython Car.

---
2021/01/20 mtanaka@sc.e.titech.ac.jp



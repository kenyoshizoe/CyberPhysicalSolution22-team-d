try:
    from raspythoncar.wr_lib2wd import WR2WD
except:
    from raspythoncar.em_lib2wd import WR2WD_emulator as WR2WD

wr = WR2WD()

while True:
  wr.led.write_red(wr.ps.left())
  wr.led.write_blue(wr.ps.right())
  wr.led.write_green(wr.ps.front())
  if wr.ps.bottom():
      wr.led.white()


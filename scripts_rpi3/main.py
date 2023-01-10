#! /usr/bin/env python3

import yaml
from threading import Thread, Lock, Event
import queue
import numpy as np
import time

import car_control

from util.webcam import webcam, img_from_dir
from util.client import Client

from raspythoncar.wr_lib2wd import WR2WD


class Client_webcam:
    def __init__(self, host='localhost', port=5556, timeout=1000, device=0, file_dir=None, zmq_mode=3):
        self.cl = Client(host, port, timeout, zmq_mode)
        if (file_dir is None):
            self.cam = webcam(device)
        else:
            self.cam = img_from_dir(file_dir)

    def classify(self):
        img = self.cam.get_img()
        data = self.cl.send_img(img)
        return data


def main():
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)
    print("param loaded")
    # setup webcam & client
    client_webcam = Client_webcam(
        host=params['client']['host'],
        port=params['client']['port'],
        device=params['client']['device'],
        timeout=params['client']['timeout'],
        zmq_mode=3
    )
    print("connected")
    # setup driver
    wr = WR2WD()
    driver = car_control.Driver(wr)

    # main loop
    try:
        while True:
            driver.update()
            if driver.state == car_control.State.WAIT_FOR_JUDGE:
                data = client_webcam.classify()
                if data is None or data['pred'] is None:
                    continue
                if data['pred'] < 0.5:
                    driver.ant()
                else:
                    driver.bee()
    except KeyboardInterrupt as e:
        print('done.')


if (__name__ == '__main__'):
    main()

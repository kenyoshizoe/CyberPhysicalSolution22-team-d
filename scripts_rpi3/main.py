#! /usr/bin/env python3

import yaml
from threading import Thread, Lock, Event
import queue
import numpy as np
import time

from util.webcam import webcam, img_from_dir
from util.client import Client

try:
    from raspythoncar.wr_lib2wd import WR2WD
except:
    pass


class Client_webcam:
    def __init__(self, host='localhost', port=5556, timeout=1000, device=0, file_dir=None, zmq_mode=3):
        self.cl = Client(host, port, timeout, zmq_mode)
        if (file_dir is None):
            self.cam = webcam(device)
        else:
            self.cam = img_from_dir(file_dir)

    def get_img(self):
        img = self.cam.get_img()
        return img

    def get_img_data(self):
        img = self.get_img()
        data = self.cl.send_img(img)
        return img, data

# https://docs.python.org/ja/3/library/queue.html


class thread_Client_webcam(Thread):
    def __init__(self, host='localhost', port=5556, timeout=1000, device=0, file_dir=None, img_only=False, zmq_mode=None):
        Thread.__init__(self)
        self.daemon = True

        self.webcam = Client_webcam(
            host=host, port=port, timeout=timeout, device=device, file_dir=file_dir, zmq_mode=zmq_mode)
        self.img_only = img_only
        self.lock = Lock()
        self.queue = queue.Queue()
        self.running = True
        Thread.start(self)

    def __del__(self):
        self.stop()

    def stop(self):
        self.running = False
        self.join()

    def run(self):
        while (self.running):
            if (self.img_only):
                img = self.webcam.get_img()
                data = None
            else:
                img, data = self.webcam.get_img_data()
                if (img is None):
                    self.running = False

            with self.lock:
                self.queue.put((img, data))
                while (self.queue.qsize() > 1):
                    #print( '***** Warning: throwing img data *****', file=sys.stderr )
                    try:
                        self.queue.get_nowait()
                    except queue.Empty:
                        pass

    def get_img_data(self):
        with self.lock:
            if (self.queue.empty()):
                img, data = None, None
            else:
                img, data = self.queue.get()
        return img, data


def main():
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)
    client_webcam = thread_Client_webcam(
        host=params['client']['host'],
        port=params['client']['port'],
        device=params['client']['device'],
        timeout=params['client']['timeout'],
        zmq_mode=3)

    try:
        wr = WR2WD()
        wr.led.off()
    except:
        wr = None

    pre_eval_time = time.time()
    try:
        while (client_webcam.running):
            # evaluation (example)
            img, data = client_webcam.get_img_data()
            if data == None:
                continue
            else:
                pre_eval_time = time.time()

            if data['pred'] < 0.5:
                wr.led.blue()
            else:
                wr.led.red()

            if (wr is not None):
                if (time.time() - pre_eval_time > 1):
                    wr.led.off()

    except KeyboardInterrupt as e:
        print('done.')


if (__name__ == '__main__'):
    main()

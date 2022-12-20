import sys
import copy
from threading import Thread, Lock, Event
import queue
import numpy as np
import argparse
import time

from util.webcam import webcam, img_from_dir
from util.client import Client

try:
    from raspythoncar.wr_lib2wd import WR2WD
except:
    pass

class Client_webcam:
    def __init__( self, host = 'localhost', port = 5556, timeout=1000, device=0, file_dir=None, zmq_mode=3 ):
        self.cl = Client( host, port, timeout, zmq_mode )
        if( file_dir is None ):
            self.cam = webcam(device)
        else:
            self.cam = img_from_dir( file_dir )

    def get_img( self ):
        img = self.cam.get_img()
        return img

    def get_img_data( self ):
        img = self.get_img()
        data = self.cl.send_img(img)
        return img, data

# https://docs.python.org/ja/3/library/queue.html
class thread_Client_webcam( Thread ):
    def __init__( self, host = 'localhost', port = 5556, timeout=1000, device=0, file_dir=None, img_only=False, zmq_mode=None ):
        Thread.__init__(self)
        self.daemon = True

        self.webcam = Client_webcam( host=host, port=port, timeout=timeout, device=device, file_dir=file_dir, zmq_mode=zmq_mode)
        self.img_only = img_only
        self.lock = Lock()
        self.queue = queue.Queue()
        self.running = True
        Thread.start(self)

    def __del__( self ):
        self.stop()

    def stop( self ):
        self.running = False
        self.join()

    def run( self ):
        while( self.running ):
            if( self.img_only ):
                img = self.webcam.get_img()
                data = None
            else:
                img, data = self.webcam.get_img_data()
                if( img is None ):
                    self.running = False

            with self.lock:
                self.queue.put( (img, data) )
                while( self.queue.qsize() > 1 ):
                    #print( '***** Warning: throwing img data *****', file=sys.stderr )
                    try:
                        self.queue.get_nowait()
                    except queue.Empty:
                        pass

    def get_img_data( self ):
        with self.lock:
            if( self.queue.empty() ):
                img, data = None, None
            else:
                img, data = self.queue.get()
        return img, data

def main( host, port, device, timeout, file_dir, zmq_mode ):
    print( 'host:', host )
    print( 'port:', port )
#    cl_webcam = Client_webcam( host=host, port=port, device=device, timeout=timeout, file_dir=file_dir, zmq_mode=zmq_mode )
    cl_webcam = thread_Client_webcam( host=host, port=port, device=device, timeout=timeout, file_dir=file_dir, zmq_mode=zmq_mode )

    try:
        wr = WR2WD()
        wr.led.off()
    except:
        wr = None

    t0 = time.time()
    code_pred = {}
    try:
        while( cl_webcam.running ):
            img, data = cl_webcam.get_img_data()

            try:
                code = data['code']
                pred = data['pred']
            except:
                pred = None

            if( pred is not None ):
                if( code in code_pred.keys() ):
                    p, w = code_pred[code]
                    code_pred[code] = [ p+data['pred'], w+1]
                else:
                    code_pred[code] = [ data['pred'], 1]

                print( data['code'], data['pred'] )
                if( wr is not None ):
                    t0 = time.time()
                    if( data['pred'] < 0.5 ):
                        wr.led.blue()
                    else:
                        wr.led.red()
            elif( wr is not None ):
                if( time.time() - t0 > 1 ):
                    wr.led.off()

    except KeyboardInterrupt as e:
        print()

    print()
    names = ['ant', 'bee']
    code_pred = sorted(code_pred.items(), key=lambda x:x[0])

    crr = 0
    num = 0
    with open( 'client_classifier.csv', 'w' ) as fout:
        for p in code_pred:
            ave = p[1][0]/p[1][1]
            id = int(ave>0.5)
            line = p[0]+', '+names[id] + ', {}'.format(ave)
            print( line )
            fout.write( line+'\n' )

            if( p[0].startswith( names[id] ) ):
                crr += 1
            num += 1

    print( 'val acc: ', crr/num )

# python client_classifier.py --host 192.168.0.170 --port 5555 -f train_imgs/
if( __name__ == '__main__' ):
    parser = argparse.ArgumentParser(description='Client Classifier')

    parser.add_argument('--host', required=True)
    parser.add_argument('--port', required=True)
    parser.add_argument('-d', '--device', type=int, default=0)
    parser.add_argument('-t', '--timeout', type=int, default=1000)
    parser.add_argument('-f', '--file_dir', default=None)
    parser.add_argument('-z', '--zmq_mode', type=int, default=3)

    args = parser.parse_args()
    main( **vars( args ) )


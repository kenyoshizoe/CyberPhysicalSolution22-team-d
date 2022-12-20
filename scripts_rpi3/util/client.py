import sys
import zmq
import json
import time
import numpy as np

import zlib
try:
   import cPickle as pickle
except:
   import pickle

try:
    # python 2
    from StringIO import StringIO as io_memory
except ImportError:
    # python 3
    from io import BytesIO as io_memory

from PIL import Image

def send_numpy_array( socket, np_array, mode=None, q=75 ):
    if( mode == 0 ):
        # https://pyzmq.readthedocs.io/en/latest/serialization.html
        md = dict(
            dtype = str(np_array.dtype),
            shape = np_array.shape,
        )
        socket.send_json(md, zmq.SNDMORE)
        socket.send(np_array)

    elif( mode == 1 ):
        p = pickle.dumps(np_array, protocol=3)
        z = zlib.compress(p)
        socket.send(z)

    elif( mode == 2 ):
        # https://blog.futurestandard.jp/entry/2017/02/27/151741
        dtype = str(np_array.dtype).encode('utf-8')
        shape = json.dumps(np_array.shape).encode('utf-8')
        array = np_array.tostring('C')
        socket.send_multipart([dtype, shape, array])

    elif( mode == 3 ):
        buffer = io_memory()
        Image.fromarray(np_array).save( buffer, 'JPEG', quality = q )
        buffer.seek(0)
        socket.send(buffer.read())

def receive_dict( socket, poller=None, timeout=1000 ):
    if( poller is None ):
        poller = zmq.Poller()
        poller.register(socket, zmq.POLLIN)

    socks = dict(poller.poll(timeout))

    data = None
    for s in socks:
        if( s == socket ):
            data = s.recv_json()

    return data

class Client:
    def __init__( self, host = 'localhost', port = 5556, timeout=1000, zmq_mode=None ):
        self.host = host
        self.port = port
        self.timeout = timeout

        self.context = None
        self.socket = None
        self.zmq_mode = zmq_mode

        hello = np.zeros( (1,1,3), dtype=np.uint8 )
        while( True ):
            data = self.send_img( hello )
            if( data is None ):
                self.disconnect()
                time.sleep(1)
            else:
                break

    def __del__( self ):
        self.disconnect()

    def connect( self ):
        if( self.context is None and self.socket is None ):
            self.context = zmq.Context()
            self.socket = self.context.socket(zmq.REQ)

            self.socket.setsockopt(zmq.LINGER, self.timeout)
            self.socket.setsockopt(zmq.RCVTIMEO, self.timeout)
            self.socket.setsockopt(zmq.SNDTIMEO, self.timeout)

            con = 'tcp://{host}:{port}'.format(host=self.host, port=self.port)
            self.socket.connect(con)

            self.poller = zmq.Poller()
            self.poller.register(self.socket, zmq.POLLIN)

    def disconnect( self ):
        if( self.socket is not None ):
            self.socket.close()
            self.socket = None

        if( self.context is not None ):
            self.context.destroy()
            self.context = None

    def send_img( self, img ):
        if( img is None ):
            return None
        self.connect()

        try:
            send_numpy_array( self.socket, img, self.zmq_mode )
            data = receive_dict( self.socket, self.poller, self.timeout )
        except zmq.error.ZMQError:
            print( '***** ERROR: ZMQ {host}:{port} *****'.format(host=self.host, port=self.port ), file=sys.stderr )
            self.disconnect()
            time.sleep(0.1)
            self.connect()
            return None

        if( data is None ):
            self.disconnect()
            time.sleep(0.1)
            self.connect()

        elif( 'Error' in data.keys() ):
            print( '***** Server Error *****', file=sys.stderr)
            print( data['Error'], file=sys.stderr)
            print( '************************', file=sys.stderr)

        return data

if( __name__ == '__main__'):
    import cv2
    # python client.py localhost 5556

    host = sys.argv[1]
    port = int(sys.argv[2])
    zmq_mode = int(sys.argv[3]) # default 3

    print( 'host:', host )
    print( 'port:', port )
    print( 'zmq_mode:', zmq_mode )

    img = cv2.imread('client.jpg')
    cl = Client( host, port, zmq_mode=zmq_mode )

    N=10
    t0 = time.time()
    for i in range(N):
        data = cl.send_img( img )
    t1 = time.time()

    print(data)
    print( (t1-t0)/10 )

    cl.disconnect()

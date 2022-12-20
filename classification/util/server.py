import sys
import cv2
import zmq
import numpy as np
import json
import datetime
import socket
import traceback
import os

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

# https://www.it-swarm-ja.tech/ja/python/python%E3%81%AEstdlib%E3%82%92%E4%BD%BF%E3%81%A3%E3%81%A6%E3%83%AD%E3%83%BC%E3%82%AB%E3%83%ABip%E3%82%A2%E3%83%89%E3%83%AC%E3%82%B9%E3%82%92%E8%A6%8B%E3%81%A4%E3%81%91%E3%82%8B/958373570/
def ip():
    return ((([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")] or [[(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]]) + ["no IP found"])[0])

def receive_numpy_array( socket, mode ):
    if( mode == 0 ):
        # https://pyzmq.readthedocs.io/en/latest/serialization.html
        try:
            md = socket.recv_json()
            msg = socket.recv()
        except KeyboardInterrupt as e:
            raise( e )
        except:
            return None

        try:
            buf = memoryview(msg)
            np_arr = np.frombuffer(buf, dtype=md['dtype'])
            np_arr.shape = md['shape']
        except:
            np_arr = None

    elif( mode == 1 ):
        try:
            z = socket.recv()
        except KeyboardInterrupt as e:
            raise( e )
        except:
            return None

        try:
            p = zlib.decompress(z)
            np_arr = pickle.loads(p)
        except:
            np_arr = None

    elif( mode == 2 ):
        # https://blog.futurestandard.jp/entry/2017/02/27/151741
        try:
            [dtype, shape, array] = socket.recv_multipart()
        except KeyboardInterrupt as e:
            raise( e )
        except:
            return None

        try:
            np_arr = np.frombuffer(array, dtype=dtype.decode('utf-8'))
            np_arr.shape = json.loads(shape.decode('utf-8'))
        except:
            np_arr = None

    elif( mode == 3 ):
        try:
            b = socket.recv()
        except KeyboardInterrupt as e:
            raise( e )
        except:
            return None

        try:
            img = Image.open( io_memory(b) )
            np_arr = np.asarray(img)
            np_arr.setflags(write=False)
        except:
            np_arr = None

    return np_arr

def draw_rect( img, r, c ):
    cv2.rectangle( img, (r.left, r.top), (r.left+r.width, r.top+r.height), c, 2 )

# https://gist.github.com/xcsrz/8938a5d4a47976c745407fe2788c813a
# https://imagingsolution.net/program/draw-outline-character/
def draw_text( img, text, pos, c, bc ):
    font = cv2.FONT_HERSHEY_SIMPLEX
    textsize = cv2.getTextSize(text, font, 1, 2)[0]

    textX = int( pos[0] - textsize[0]/2 ) # center
    textY = int( pos[1] - textsize[1]/2 )  # bottom
    cv2.putText(img, text, (textX, textY), font, 1, bc, 6, cv2.LINE_AA)
    cv2.putText(img, text, (textX, textY), font, 1,  c, 2, cv2.LINE_AA)


def server_start( port=5556, func=None, verbose=False, imshow=False, imfile=None, vs_str=['dog', 'cat'], zmq_mode = None ):
    print( 'host: ', ip() )
    print( 'port: ', port )
    bind = f'tcp://*:{port}'

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.setsockopt(zmq.LINGER, 10)
    socket.bind(bind)
    print("Server startup.")

    while( True ):
        try:
            img = receive_numpy_array( socket, zmq_mode )
        except KeyboardInterrupt:
            print()
            break

        if( img is None ):
            '''
            socket.close()
            socket = context.socket(zmq.REP)
            socket.setsockopt(zmq.LINGER, 10)
            socket.bind(bind)
            '''
            error_message = '***** ERROR: The client may send a wrong data. Check zmq_mode: {} *****'.format(zmq_mode)
            print(error_message, file=sys.stderr)
            data = {'Error':error_message}
            socket.send_json(data)

        else:
            print('-----')
            print( 'recv at', datetime.datetime.now() )

            if( img.shape == (1,1,3) ):
                data = {'Hello':img.shape}
            else:
                try:
                    data = func( img )
                except:
                    error_message = traceback.format_exc()
                    print( '***** ERROR in func *****', file=sys.stderr )
                    print( error_message, file=sys.stderr )
                    print( '*************************', file=sys.stderr )
                    data = {'Error':error_message}

            socket.send_json(data)
            print( 'send at', datetime.datetime.now() )

            try:
                img0 = img.copy()

                if( verbose ):
                    print(json.dumps(data, indent=2))

                if( imshow or imfile ):
                    c = (255,0,0) #BGR, blur
                    bc = (192,192,192)
                    try:
                        draw_rect( img, data['rect'], c )
                    except:
                        pass

                    try:
                        text = data['code']
                        r = data['rect']
                        pos = (r.left+r.width/2, r.top+r.height)
                        draw_text( img, text, pos, c, bc )
                    except:
                        pass

                    try:
                        if( data['pred'] < 0.5 ):
                            c = (255,255,  0) #BGR cyan for dog
                        else:
                            c = (255,  0,255) #BGR magenta for cat
                        bc = (64,64,64)
                    except:
                        c = (255,0,0) #BGR blue
                        bc = (192,192,192)

                    try:
                        draw_rect( img, data['roi_rect'], c )
                    except:
                        pass

                    try:
                        text = vs_str[0] if data['pred'] < 0.5 else vs_str[1]
                        text = text + ':{:5.3f}'.format(data['pred'])
                        r = data['roi_rect']
                        pos = (r.left+r.width/2, r.top+r.height)
                        draw_text( img, text, pos, c, bc )

                    except:
                        pass

                if( imshow ):
                    cv2.imshow('Hit space key to save image.',img)
                    #cv2.waitKey(1)
                    key = cv2.waitKey(1) & 0xff
                    if( key == ord(' ') ):
                        if( os.path.exists('./capture') == False):
                            os.mkdir('./capture')
                        cv2.imwrite('./capture/'+datetime.datetime.now().strftime("%Y%m%d-%H%M%S")+'.jpg',img0)


                if( imfile is not None ):
                    cv2.imwrite(imfile,img)

            except:
                error_message = traceback.format_exc()
                print( '***** ERROR in server *****', file=sys.stderr )
                print( error_message, file=sys.stderr )
                print( '*************************', file=sys.stderr )

    print( 'Closing socket' )
    socket.close()
    context.destroy()
    if( imshow ):
        cv2.destroyAllWindows()
    print( 'bye' )

if( __name__ == '__main__' ):
    # python server.py 5556
    from pyzbar.locations import Rect

    def func( img ):
        data = {'mean': img.astype('float').mean().tolist()}
        data['Rects'] = [[Rect(10,10,20,10), (0,255,0)], [Rect(30,30,20,40), (255,0,0)]]
        return data

    port = int(sys.argv[1])
    server_start( port, func, verbose=True, imfile='server.jpg' )

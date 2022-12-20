import cv2
import glob
import random

# https://qiita.com/iwatake2222/items/b8c442a9ec0406883950
# http://project12513.blog-fps.com/raspberrypi%E9%96%8B%E7%99%BA/%E3%83%A9%E3%82%BA%E3%83%91%E3%82%A4%E3%81%A7opencv%E3%81%AE%E5%87%A6%E7%90%86%E3%82%92%E9%80%9F%E3%81%8F%E3%81%99%E3%82%8B
# https://ja.laptopwide.com/260598-how-to-get-the-latest-MUTWDL

class webcam:
    def __init__( self, device=0, frame_width=1280, frame_height=720, n_grab=2 ):
        self.device = device
        self.capture = cv2.VideoCapture(self.device)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, frame_width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, frame_height)
        self.capture.set(cv2.CAP_PROP_FPS, 10)
        self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.__ret = None
        self.n_grab = n_grab

    @property
    def ret(self):
        return self.__ret

    def __del__( self ):
        self.capture.release()

    def get_img( self ):
        for i in range(self.n_grab):
            self.capture.grab()
        self.__ret, img = self.capture.read()
        return img

class img_from_dir:
    def __init__( self, dir ):
        self.dir = dir

        files = glob.glob( self.dir + '/*' )
        self.files0 = files

        self.files = self.files0.copy()
        #random.shuffle( self.files )
        self.files.sort()

    def get_img( self ):
        if( len(self.files) == 0 ):
            return None
#            self.files = self.files0.copy()
#            random.shuffle( self.files )

        file = self.files.pop()
        img = cv2.imread( file )
        return img

if( __name__ == '__main__' ):
    cam = webcam()
    img = cam.get_img()
    cv2.imwrite( 'webcam.jpg', img )

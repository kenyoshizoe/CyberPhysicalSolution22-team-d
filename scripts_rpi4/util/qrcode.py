import os
import cv2
import pyqrcode
import barcode
from pyzbar.pyzbar import decode
from pyzbar.locations import Rect
import numpy as np

# https://qiita.com/igor-bond16/items/0dbef691a71c2e5e37d7
def generate( ustr, tmp_filename='__qrcode_generate', scale=6, remove=True):
    qr = pyqrcode.QRCode(ustr)
    qr.png(tmp_filename+'.png',scale=scale)
    qr_img = cv2.imread(tmp_filename+'.png')
    if( remove ):
        os.remove( tmp_filename+'.png' )
    return qr_img

def detect( img, th_area=20*20 ):
    data = decode( img )
    if( data is None ):
        return None, None

    if( len(data) == 0 ):
        return None, None
    elif( len(data) == 1 ):
        data = data[0]
    else:
        area = [ d.rect.width * d.rect.height for d in data ]
        p = np.argmax(area)
        data = data[p]

    code = data[0].decode(encoding='utf-8')
    rect = data.rect

    if( rect.width * rect.height < th_area ):
        return code, None

    return code, rect

def is_inside( roi, img ):
    s = img.shape
    return roi.top >= 0 and roi.top + roi.height < s[0] and \
        roi.left >= 0 and roi.left + roi.width < s[1]

def detect_roi( img, size_ratio=None, gap_ratio=None, th_area=None ):
    if( size_ratio is None ):
        size_ratio = (1.6, 1.6)
    if( gap_ratio is None ):
        gap_ratio = 0.25
    if( th_area is None ):
        th_area = 20*20
    code, rect = detect( img, th_area )

    if( rect is None ):
        return (code, None), (None, None)

    else:
        roi_width = int(rect.width * size_ratio[0])
        roi_height = int(rect.height * size_ratio[1])

        roi_top = int( rect.top - roi_height - rect.height*gap_ratio )
        roi_left = int(rect.left - (roi_width - rect.width)/2)

        roi_rect = Rect( left=roi_left, top=roi_top, width=roi_width, height=roi_height )
        if( is_inside( roi_rect, img ) ):
            roi = img[ roi_rect.top:roi_rect.top+roi_rect.height, roi_rect.left:roi_rect.left+roi_width,:]
        else:
            return (code, rect), (None, None)

    return (code, rect), (roi, roi_rect)

if( __name__ == '__main__' ):
    import glob

    os.makedirs('detect_roi', exist_ok=True)
    files = glob.glob( '../train_imgs/*.jpg' )
    files.sort()
    for file in files:
        img = cv2.imread( file )
        (code, rect), (roi, roi_rect) = detect_roi( img )
        basename = os.path.basename(file)
        print( basename, code, rect, roi_rect )

        cv2.rectangle( img, (rect.left,rect.top), (rect.left+rect.width,rect.top+rect.height), (0,255,0), 2 )
        cv2.rectangle( img, (roi_rect.left,roi_rect.top), (roi_rect.left+roi_rect.width,roi_rect.top+roi_rect.height), (0,0,255), 2 )

        cv2.imwrite( 'detect_roi/'+basename, img )

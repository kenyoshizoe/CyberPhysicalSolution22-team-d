#! /usr/bin/python3
import sys

from pyzbar.locations import Rect
import numpy as np
import argparse

from img2feat import CNN
from util.server import server_start
from util.regression import load_model, predict
from util.qrcode import detect_roi


###### EDIT HERE #################################
def classify_roi(net, model, code, rect, roi, roi_rect):
    if (roi is None):
        return None

    x = net([roi])
    x = predict(model, x)
    x = float(x[0])
    return x

    '''
    # Simple TTA
    mirror = np.fliplr( roi ).copy()
    x = net([roi,mirror])
    x = predict( model, x )
    return float(x.mean())
    '''

##################################################


class Classifier:
    def __init__(self, network='alexnet', model_name='model', size_ratio=None, gap_ratio=None, th_area=None):
        self.size_ratio = size_ratio
        self.gap_ratio = gap_ratio
        self.th_area = th_area

        self.net = CNN(network)
        model_name = model_name + '_' + network + '.pkl'
        self.model = load_model(model_name)

    def __call__(self, img):
        (code, rect), (roi, roi_rect) = detect_roi(
            img, size_ratio=self.size_ratio, gap_ratio=self.gap_ratio, th_area=self.th_area)

        data = {
            'code': code,
            'rect': rect,
            'roi_rect': roi_rect,
            'pred': classify_roi(self.net, self.model, code, rect, roi, roi_rect),
        }

        return data


def main(port, network, model_name, imshow, imfile, verbose, vs_str, zmq_mode):
    print(model_name + '_' + network + '.pkl')
    dnn = Classifier(network=network, model_name=model_name)
    server_start(port, dnn, verbose=verbose, imfile=imfile,
                 imshow=imshow, vs_str=vs_str, zmq_mode=zmq_mode)


# python server_classifier.py -v --port 5555
if (__name__ == '__main__'):
    parser = argparse.ArgumentParser(description='Server')

    parser.add_argument('--imshow', action='store_true', default=False)
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('--imfile', default='server.jpg')

    parser.add_argument('-n', '--network', default='alexnet')
    parser.add_argument('-m', '--model_name', default='model')
    parser.add_argument('-p', '--port', type=int, required=True)
    parser.add_argument('-z', '--zmq_mode', type=int, default=3)

    parser.add_argument('--vs_str', nargs=2, default=['ant', 'bee'])

    args = parser.parse_args()
    main(**vars(args))

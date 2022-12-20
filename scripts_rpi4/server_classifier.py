#! /usr/bin/python3
import sys
import yaml
import pickle

from pyzbar.locations import Rect
import numpy as np

from img2feat import CNN
from util.server import server_start
from util.regression import load_model, predict
from util.qrcode import detect_roi
from evaluation import evaluation

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
    def __init__(self, params, size_ratio=None, gap_ratio=None, th_area=None):
        self.params = params

        self.size_ratio = size_ratio
        self.gap_ratio = gap_ratio
        self.th_area = th_area

        # setup network
        self.net = CNN(params['network'])
        # load model
        model_name = params['name'] + '_' + params['network'] + '.pkl'
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


def main(params):
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)
    # load model
    filename = params['name'] + '_' + params['network'] + '.pkl'
    model = pickle.load(open('model/' + filename, 'rb'))
    # steup network
    net = CNN(params['network'])

    classifier = Classifier()

    server_start(5555, dnn, verbose=verbose, imfile=imfile,
                 imshow=imshow, vs_str=vs_str, zmq_mode=zmq_mode)


# python server_classifier.py -v --port 5555
if (__name__ == '__main__'):

    main()

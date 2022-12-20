#! /usr/bin/env python3
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


class Classifier:
    def __init__(self, params, size_ratio=None, gap_ratio=None, th_area=None):
        self.params = params

        self.size_ratio = size_ratio
        self.gap_ratio = gap_ratio
        self.th_area = th_area

        # setup network
        self.net = CNN(params['network'])

        # load model
        filename = params['name'] + '_' + params['network'] + '.pkl'
        self.model = pickle.load(open('model/' + filename, 'rb'))

    def __call__(self, img):
        (code, rect), (roi, roi_rect) = detect_roi(
            img, size_ratio=self.size_ratio, gap_ratio=self.gap_ratio, th_area=self.th_area)

        data = {
            'code': code,
            'rect': rect,
            'roi_rect': roi_rect,
            'pred': evaluation(self.model, self.net, roi, code, self.params['evaluation']),
        }

        return data


def main():
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)

    # steup network
    classifier = Classifier(params)
    server_start(5555, classifier, verbose=False, imfile='server.jpg',
                 imshow=params['server']['preview'], vs_str=['ant', 'bee'], zmq_mode=3)


# python server_classifier.py -v --port 5555
if (__name__ == '__main__'):

    main()

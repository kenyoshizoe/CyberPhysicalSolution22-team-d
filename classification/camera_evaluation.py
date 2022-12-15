#! /usr/bin/env python3
import os
import glob
import cv2
import yaml
import pickle
import datetime

from img2feat import CNN

import util.preprocessing as pre
from util.qrcode import detect_roi
from util.progressbar import print_progress
from evaluation import evaluation

if (__name__ == '__main__'):
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)
    eval_params = params['evaluation']
    eval_params['network'] = params['network']
    eval_params['name'] = params['name']

    # load model
    filename = params['name'] + '_' + params['network'] + '.pkl'
    model = pickle.load(open('model/' + filename, 'rb'))
    if model is None:
        print('couldnt load model')
        exit()

    # setup CNN
    net = CNN(eval_params['network'])

    # setup camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print('camera couldnt open')
        exit()

    param = {
        'print_result': True,
        'have_qr': False,
        'preview': False,
        'equalization': {
            'eqalize_s': True,
            'eqalize_v': False
        }
    }

    while True:
        # capture
        ret, frame = cap.read()
        if frame is None:
            continue

        (code, rect), (roi, roi_rect) = detect_roi(frame)
        if roi is not None:
            y = evaluation(model, net, frame, code, param)
            if y is None:
                continue

            # visualization
            color = (255, 255, 255)
            label = pre.code2label(code)
            if label == (0.5 < y):
                color = (0, 0, 255)
            elif label is not None:
                color = (255, 0, 0)

            pt1 = (roi_rect.left, roi_rect.top)
            pt2 = (roi_rect.left + roi_rect.width,
                   roi_rect.top + roi_rect.height)
            cv2.rectangle(frame, pt1, pt2, color, 3)
            cv2.putText(frame, code, (roi_rect.left + 5,
                        roi_rect.top + roi_rect.height - 5),
                        cv2.FONT_HERSHEY_PLAIN, 2, (255, 255, 255), 3)

        # visualization
        cv2.imshow("frame", frame)
        key = cv2.waitKey(1)
        if key == ord(' '):
            cv2.imwrite('capture/' + code + '-' +
                        datetime.datetime.now().isoformat() + '.jpg', frame)
        if key == ord('q'):
            break
    cap.release()

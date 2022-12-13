#! /usr/bin/python3
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

IMG_SIZE = (224, 224)
PRINT_RESULT = True


def evaluation(model,  params):
    net = CNN(params['network'], img_size=IMG_SIZE)

    data_num = 0
    correct_num = 0

    code_y = []
    result_y = []

    files = glob.glob('{}/*'.format(params['directory']))
    for i, file in enumerate(files):
        basename = os.path.basename(file)
        img = cv2.imread(file)

        if img is None:
            continue

        label = None

        if params['have_qr']:
            (code, rect), (img, roi_rect) = detect_roi(img)
            label = pre.code2label
            if img is None:
                continue
        else:
            label = pre.code2label(basename)

        if img is None or label is None:
            continue

        img = pre.equalization(img, params['equalization'])
        img = pre.make_squared(img, params['make_squared'])

        if params['preview']:
            cv2.imshow('evaluated iage', img)
            cv2.waitKey(10)

        x = net([img])
        y = model.predict(x)

        data_num += 1
        if basename.startswith('ant') == (y[0] < 0.5):
            if params['print_result']:
                print(basename, 'o')
            correct_num += 1
        else:
            if params['print_result']:
                print(basename, 'x')

        if not params['print_result']:
            print_progress(i + 1, len(files))
    print(f'\naccuracy:{correct_num / data_num * 100} %')


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

    while True:
        # capture
        ret, frame = cap.read()
        if frame is None:
            continue

        (code, rect), (roi, roi_rect) = detect_roi(frame)
        if roi is not None:
            roi = pre.equalization(frame, eval_params['equalization'])

            x = net([roi])
            y = model.predict(x)

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

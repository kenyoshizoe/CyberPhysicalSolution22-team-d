#! /usr/bin/python3
import os
import glob
import cv2
import yaml
import pickle

from img2feat import CNN

import util.preprocessing as pre
from util.qrcode import detect_roi

IMG_SIZE = (224, 224)
PRINT_RESULT = True


def evaluation(model,  params):
    net = CNN(params['network'], img_size=IMG_SIZE)

    data_num = 0
    correct_num = 0

    code_y = []
    result_y = []

    files = glob.glob('{}/*'.format(params['directory']))
    for file in files:
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
            if PRINT_RESULT:
                print(basename, ':o:')
            correct_num += 1
        else:
            if PRINT_RESULT:
                print(basename, ':x:')

    print(f'accuracy:{correct_num / data_num * 100} %')


if (__name__ == '__main__'):
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)

    # load model
    filename = params['name'] + '_' + params['network'] + '.pkl'
    model = pickle.load(open('model/' + filename, 'rb'))

    if model is None:
        print('couldnt load model')
        exit()

    base_params = params['evaluation']
    base_params['network'] = params['network']
    base_params['name'] = params['name']

    PRINT_RESULT = False

    for setting in params['evaluation_settings']:
        eval_params = base_params.copy()
        eval_params.update(params[setting])
        # evaluation
        print("--- evaluation {} ---".format(setting))
        evaluation(model, eval_params)

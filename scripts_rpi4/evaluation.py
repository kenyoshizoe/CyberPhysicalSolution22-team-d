#! /usr/bin/env python3
import os
import glob
import cv2
import yaml
import pickle

from img2feat import CNN

import util.preprocessing as pre
from util.qrcode import detect_roi
from util.progressbar import print_progress

IMG_SIZE = (224, 224)
PRINT_RESULT = True


def evaluation_from_param(model,  params):
    net = CNN(params['network'], img_size=IMG_SIZE)

    data_num = 0
    correct_num = 0

    code_y = []
    result_y = []

    files = glob.glob('{}/*'.format(params['directory']))
    for i, file in enumerate(files):
        basename = os.path.basename(file)
        img = cv2.imread(file)

        y = evaluation(model, net, img, basename, params)
        if y is None:
            continue

        data_num += 1
        if basename.startswith('ant') == (y[0] < 0.5):
            if params['print_result']:
                print('⭕', basename)
            correct_num += 1
        else:
            if params['print_result']:
                print('❌', basename)

        if not params['print_result']:
            print_progress(i + 1, len(files))
    print(f'\naccuracy:{correct_num / data_num * 100} %')

def evaluation(model, net, img, code, params):
    if img is None:
        return
    label = None
    if params['have_qr']:
        (code, rect), (img, roi_rect) = detect_roi(img)
        if code is None or img is None:
            return None
        label = pre.code2label(code)
    else:
        label = pre.code2label(code)

    if img is None:
        return None

    # 前処理
    img = pre.equalization(img, params['equalization'])
    if not params['have_qr']:
        img = pre.make_squared(img, params['make_squared'])

    # プレビュー
    if params['preview']:
        cv2.imshow('evaluated iage', img)
        cv2.waitKey(10)

    x = net([img])
    y = model.predict(x)

    return y


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
        evaluation_from_param(model, eval_params)

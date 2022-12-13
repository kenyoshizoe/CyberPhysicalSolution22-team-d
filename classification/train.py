#! /usr/bin/python3
import os
import glob
import numpy as np
import cv2
import yaml
import sklearn
import pickle

from img2feat import CNN
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import BaggingRegressor
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC, LinearSVC

from util.qrcode import detect_roi
import util.preprocessing as pre

IMG_SIZE = (224, 224)


def extract_features(net, img):
    augmented_data = []
    for i in [img, np.fliplr(img).copy()]:
        augmented_data.append(i)
        augmented_data.append(cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE))
        augmented_data.append(cv2.rotate(img, cv2.ROTATE_180))
        augmented_data.append(cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE))
    f = net(augmented_data)
    return f


def train_model(X, Y):
    # model = LinearRegression()
    # model = sklearn.neighbors.KNeighborsClassifier(3)
    model = make_pipeline(
        StandardScaler(), LinearSVC(random_state=0, tol=1e-5))
    # model = make_pipeline(StandardScaler(), SVC(gamma='auto'))
    model.fit(X, Y)
    return model


def train(params):
    net = CNN(params['network'])

    X = None
    Y = None

    files = glob.glob('{}/*'.format(params['directory']))
    for file in files:
        # 画像 / ラベル読み込み
        basename = os.path.basename(file)
        img = cv2.imread(file)
        y = pre.code2label(basename)
        # 例外処理
        if img is None or y is None:
            continue
        # 前処理
        img = pre.equalization(img, params['equalization'])
        img = pre.make_squared(img, params['make_squared'])
        # プレビュー
        if params['preview']:
            cv2.imshow("trained image", img)
            cv2.waitKey(10)
        # 特徴量抽出
        f = extract_features(net, img)
        nb_f = f.shape[0]
        y = np.ones((nb_f,), dtype=np.int) * y
        X = f if (X is None) else np.concatenate((X, f), axis=0)
        Y = y if (Y is None) else np.concatenate((Y, y), axis=0)

        print(basename)

    # 学習
    model = train_model(X, Y)

    # 保存
    filename = params['name'] + '_' + params['network'] + '.pkl'
    pickle.dump(model, open('model/' + filename, 'wb'))

    Ypred = model.predict(X)

    acc = sklearn.metrics.accuracy_score(Y, (Ypred > 0.5).astype(np.int))
    print('fitting accuracy:', acc)
    return model


if (__name__ == '__main__'):
    # load params
    params = None
    with open('config/default.yaml') as f:
        params = yaml.safe_load(f)

    # extract params
    train_params = params['train']
    train_params['network'] = params['network']
    train_params['name'] = params['name']

    # print(train_params)
    # print(eval_params)

    print("--- train ---")
    trained_model = train(train_params)

import cv2
import numpy as np

IMG_SIZE = (224, 224)

def code2label(code):
    if (len(code) < 3):
        return None
    if (code[:3].lower() in ['dog', 'ant']):
        label = 0
    elif (code[:3].lower() in ['cat', 'bee']):
        label = 1
    else:
        label = None
    return label

def make_squared(img, params):
    if params['method'] == "WHITE_BG":
        size = max(img.shape[0], img.shape[1])
        squared_img = np.zeros((size, size, 3), np.uint8)
        squared_img += 255
        squared_img[0:img.shape[0], 0:img.shape[1]] = img
        squared_img = cv2.resize(squared_img, IMG_SIZE)
        return squared_img
    elif params['method'] == "CUTOFF":
        size = min(img.shape[0], img.shape[1])
        top_bound = img.shape[0] // 2 - size // 2
        bottom_bound = img.shape[0] // 2 + size // 2
        left_bound = img.shape[1] // 2 - size // 2
        right_bound = img.shape[1] // 2 + size // 2

        squared_img = img[top_bound:bottom_bound, left_bound:right_bound]
        squared_img = cv2.resize(squared_img, IMG_SIZE)
        return squared_img
    return img


def equalization(img, params):
    if params['method'] == "HSV_HIST":
        h1, s1, v1 = cv2.split(cv2.cvtColor(
            img, cv2.COLOR_BGR2HSV))  # 色空間をBGRからHSVに変換

        s2 = cv2.equalizeHist(s1) if params['equalize_s'] else s1
        v2 = cv2.equalizeHist(v1) if params['equalize_v'] else v1

        eqh_hsv = cv2.cvtColor(cv2.merge((h1, s2, v2)), cv2.COLOR_HSV2BGR)
        return eqh_hsv

    if params['equalization_method'] == "CLAHE":
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        b1, g1, r1 = cv2.split(img)
        b2 = clahe.apply(b1)
        g2 = clahe.apply(g1)
        r2 = clahe.apply(r1)
        return cv2.merge((b2, g2, r2))
    return img


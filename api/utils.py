import cv2
import numpy as np

def extract_face_embedding(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    if len(faces) == 0:
        return None

    x, y, w, h = faces[0]
    face = gray[y:y+h, x:x+w]
    face = cv2.resize(face, (100, 100))

    hist = cv2.calcHist([face], [0], None, [256], [0, 256]).flatten()
    hist = hist / np.linalg.norm(hist)
    return hist.astype(np.float32)

import cv2
from PIL import Image

cap = cv2.VideoCapture(0)

ret, frame = cap.read()

cv2.imwrite("snapshot.jpg", frame)


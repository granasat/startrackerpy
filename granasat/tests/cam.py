# some cam tests
import cv2


cam = cv2.VideoCapture(0, cv2.CAP_V4L2)
# cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)
# cam.set(cv2.CAP_PROP_EXPOSURE, 900)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 960)
ret, frame = cam.read()
cv2.imwrite('cv2_image.TIFF', frame)
cam.release()

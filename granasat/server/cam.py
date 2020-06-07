import os
import cv2
from filelock import FileLock


# TODO remove it
class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args,
                                                                 **kwargs)
        return cls._instances[cls]


class Cam():
    """ .
    """
    params_dict = {
        'brightness': cv2.CAP_PROP_BRIGHTNESS,
        'gamma': cv2.CAP_PROP_GAMMA,
        'gain': cv2.CAP_PROP_GAIN,
        'exposure': cv2.CAP_PROP_EXPOSURE,
    }

    def __init__(self):
        self._id = 0
        self._lock = FileLock("/tmp/cam.lock")

    def read(self):
        """ Returns the cv2 camera object
        """
        self._lock.acquire(timeout=10)
        cam = cv2.VideoCapture(self._id)
        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)
        ret, frame = cam.read()
        self._lock.release()

        return ret, frame

    def get_camera_params(self):
        """ Returns the parameters read from the camera
        """
        self._lock.acquire(timeout=10)
        cam = cv2.VideoCapture(self._id)
        response = {
            'brightness': cam.get(cv2.CAP_PROP_BRIGHTNESS),
            'gamma': cam.get(cv2.CAP_PROP_GAMMA),
            'gain': cam.get(cv2.CAP_PROP_GAIN),
            'exposure': cam.get(cv2.CAP_PROP_EXPOSURE),
        }
        self._lock.release()

        return response

    def set_camera_params(self, params):
        self._lock.acquire(timeout=10)
        cam = cv2.VideoCapture(self._id)
        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)
        for param, value in params.items():
            if value is not None:
                cam.set(self.params_dict[param], value)
        self._lock.release()
import os
import cv2
from filelock import FileLock
import numpy


class Cam():
    """Class to control the camera device
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

    def lock_acquire(self, timeout=10) -> None:
        """Acquire a lock to use the camera device

        :param timeout: Time to wait for the lock; defaults to 10 seconds.
        """
        self._lock.acquire(timeout=timeout)

    def lock_release(self) -> None:
        """Release the lock
        """
        self._lock.release()

    def read(self) -> (int, numpy.ndarray):
        """Returns the cv2 camera object

        :return: (ret, frame)
        """
        cam = cv2.VideoCapture(self._id)
        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)
        ret, frame = cam.read()

        return ret, frame

    def get_camera_params(self) -> {}:
        """Returns the parameters read from the camera

        :return: Dictionary with the parameters' values
        """
        cam = cv2.VideoCapture(self._id)
        response = {
            'brightness': cam.get(cv2.CAP_PROP_BRIGHTNESS),
            'gamma': cam.get(cv2.CAP_PROP_GAMMA),
            'gain': cam.get(cv2.CAP_PROP_GAIN),
            'exposure': cam.get(cv2.CAP_PROP_EXPOSURE),
        }

        return response

    def set_camera_params(self, params) -> None:
        """Set camera parameters

        :param params: Dictionary with the parameters to set
        """
        cam = cv2.VideoCapture(self._id)
        cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        cam.set(cv2.CAP_PROP_AUTO_EXPOSURE, 1.0)
        for param, value in params.items():
            if value is not None:
                cam.set(self.params_dict[param], value)

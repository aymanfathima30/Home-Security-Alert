"""
CameraStream
------------
Wraps the Raspberry Pi camera module (picamera2) with a thread-safe
frame buffer for real-time access by the monitoring loop and GUI.
"""

import threading
import logging
import numpy as np

try:
    from picamera2 import Picamera2
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)


class CameraStream:
    def __init__(self, resolution: tuple = (640, 480), framerate: int = 24):
        self.resolution = resolution
        self.framerate = framerate
        self._frame = None
        self._lock = threading.Lock()
        self._running = False

        if PICAMERA_AVAILABLE:
            self._cam = Picamera2()
            config = self._cam.create_preview_configuration(
                main={"size": resolution, "format": "RGB888"}
            )
            self._cam.configure(config)
            logger.info("Using Raspberry Pi camera module (picamera2).")
        elif CV2_AVAILABLE:
            self._cam = cv2.VideoCapture(0)
            self._cam.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
            self._cam.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
            logger.info("picamera2 not found — falling back to OpenCV webcam.")
        else:
            raise RuntimeError("No camera backend found. Install picamera2 or opencv-python.")

    def start(self):
        self._running = True
        if PICAMERA_AVAILABLE:
            self._cam.start()
        logger.info("Camera stream started.")
        self._capture_loop()

    def _capture_loop(self):
        while self._running:
            if PICAMERA_AVAILABLE:
                frame = self._cam.capture_array()
            elif CV2_AVAILABLE:
                ret, frame = self._cam.read()
                if not ret:
                    continue

            with self._lock:
                self._frame = frame

    def read_frame(self) -> np.ndarray | None:
        with self._lock:
            return self._frame.copy() if self._frame is not None else None

    def stop(self):
        self._running = False
        if PICAMERA_AVAILABLE:
            self._cam.stop()
        elif CV2_AVAILABLE:
            self._cam.release()
        logger.info("Camera stream stopped.")

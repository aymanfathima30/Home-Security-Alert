"""
FaceRecogniser
--------------
Integrates facial recognition into the camera feed using the `face_recognition`
library (built on dlib). This module compares detected faces against a library
of known residents/authorised individuals and flags unknown visitors.

HOW IT CONNECTS TO THE CAMERA:
  main.py calls `face_recogniser.recognise(frame)` on every motion-triggered frame.
  The frame is a raw NumPy array captured directly from the CameraStream —
  the same live video feed displayed in the GUI.

  Flow:
    CameraStream.read_frame()  →  MotionDetector.detect()
                                          ↓ (motion detected)
                               FaceRecogniser.recognise(frame)
                                          ↓
                               AlertManager.trigger_alert()   (if unknown)
"""

import os
import logging
import numpy as np
from pathlib import Path

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    logging.warning("face_recognition library not installed. Recognition will be disabled.")

logger = logging.getLogger(__name__)


class FaceRecogniser:
    def __init__(self, known_faces_dir: str, tolerance: float = 0.5, use_gpu: bool = False):
        """
        Parameters
        ----------
        known_faces_dir : path to folder of known-person images
                          One subfolder per person, named with the person's name.
                          e.g. data/known_faces/Alice/photo1.jpg
        tolerance       : lower = stricter matching (0.5 is a good default)
        use_gpu         : set True on a CUDA-capable device (not Raspberry Pi)
        """
        self.tolerance = tolerance
        self.use_gpu = use_gpu
        self.known_encodings = []
        self.known_names = []

        if FACE_RECOGNITION_AVAILABLE:
            self._load_known_faces(known_faces_dir)
            logger.info(f"Loaded {len(self.known_names)} known face(s): {self.known_names}")
        else:
            logger.warning("Running without face recognition — all motion will log as 'no_face'.")

    def _load_known_faces(self, directory: str):
        """
        Load and encode all known faces from the faces directory.
        Supports .jpg, .jpeg, .png files.
        """
        base = Path(directory)
        if not base.exists():
            logger.warning(f"Known faces directory not found: {directory}")
            return

        for person_dir in base.iterdir():
            if not person_dir.is_dir():
                continue
            name = person_dir.name
            for img_path in person_dir.glob("*.jpg"):
                image = face_recognition.load_image_file(str(img_path))
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_encodings.append(encodings[0])
                    self.known_names.append(name)
                    logger.debug(f"Encoded face for {name} from {img_path.name}")

    def recognise(self, frame: np.ndarray) -> dict:
        """
        Detect and recognise faces in a camera frame.

        Parameters
        ----------
        frame : NumPy array (H × W × 3, RGB) from CameraStream

        Returns
        -------
        dict with keys:
          status       : "known" | "unknown" | "no_face"
          name         : matched name (if known), else None
          face_count   : number of faces detected
          locations    : list of (top, right, bottom, left) bounding boxes
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return {"status": "no_face", "name": None, "face_count": 0, "locations": []}

        # Downsample to 1/4 resolution for faster processing on Pi
        small_frame = frame[::2, ::2]

        face_locations = face_recognition.face_locations(small_frame, model="hog")
        if not face_locations:
            return {"status": "no_face", "name": None, "face_count": 0, "locations": []}

        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        for encoding, location in zip(face_encodings, face_locations):
            matches = face_recognition.compare_faces(
                self.known_encodings, encoding, tolerance=self.tolerance
            )
            if True in matches:
                matched_idx = matches.index(True)
                name = self.known_names[matched_idx]
                return {
                    "status": "known",
                    "name": name,
                    "face_count": len(face_locations),
                    "locations": face_locations,
                }

        # Face detected but no match in known library
        return {
            "status": "unknown",
            "name": None,
            "face_count": len(face_locations),
            "locations": face_locations,
        }

    def add_known_face(self, image_path: str, name: str) -> bool:
        """Dynamically add a new face to the known library (no restart required)."""
        if not FACE_RECOGNITION_AVAILABLE:
            return False
        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                self.known_encodings.append(encodings[0])
                self.known_names.append(name)
                logger.info(f"Added {name} to known faces library.")
                return True
        except Exception as e:
            logger.error(f"Failed to add face for {name}: {e}")
        return False

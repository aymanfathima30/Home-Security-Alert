"""
Home Security Alert System — Raspberry Pi IoT
Entry point: initialises camera, motion detector, and GUI alert interface.
"""

import threading
import time
import logging
from camera.stream import CameraStream
from detection.motion_detector import MotionDetector
from detection.face_recogniser import FaceRecogniser
from alerts.alert_manager import AlertManager
from gui.dashboard import SecurityDashboard

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main():
    logger.info("Initialising Home Security Alert System...")

    # Initialise subsystems
    camera = CameraStream(resolution=(640, 480), framerate=24)
    motion_detector = MotionDetector(sensitivity=0.02, min_area=500)
    face_recogniser = FaceRecogniser(
        known_faces_dir="data/known_faces",
        tolerance=0.5,
        use_gpu=False  # Raspberry Pi — CPU inference
    )
    alert_manager = AlertManager(
        email_cfg="config/email.json",
        sms_cfg="config/sms.json",
        snapshot_dir="data/snapshots"
    )

    # Start camera stream in background thread
    camera_thread = threading.Thread(target=camera.start, daemon=True)
    camera_thread.start()
    logger.info("Camera stream started.")

    # Start security monitoring loop in background thread
    monitor_thread = threading.Thread(
        target=monitoring_loop,
        args=(camera, motion_detector, face_recogniser, alert_manager),
        daemon=True
    )
    monitor_thread.start()
    logger.info("Monitoring loop started.")

    # Launch GUI dashboard (blocks main thread)
    dashboard = SecurityDashboard(camera, alert_manager)
    dashboard.run()


def monitoring_loop(camera, motion_detector, face_recogniser, alert_manager):
    """
    Core security loop:
      1. Read frame
      2. Detect motion
      3. If motion → run face recognition
      4. If unknown face → trigger alert
    """
    logger.info("Security monitoring active.")
    while True:
        frame = camera.read_frame()
        if frame is None:
            time.sleep(0.05)
            continue

        # Step 1: Motion detection
        motion_detected, motion_region = motion_detector.detect(frame)

        if motion_detected:
            logger.info(f"Motion detected — region: {motion_region}")

            # Step 2: Face recognition on motion region
            recognition_result = face_recogniser.recognise(frame)

            if recognition_result["status"] == "unknown":
                logger.warning("Unknown individual detected — triggering alert.")
                alert_manager.trigger_alert(
                    frame=frame,
                    event_type="UNKNOWN_PERSON",
                    details=recognition_result
                )
            elif recognition_result["status"] == "known":
                name = recognition_result["name"]
                logger.info(f"Recognised: {name} — no alert.")
            else:
                # No face found but motion present (could be animal, object)
                logger.info("Motion with no face detected — logging event.")
                alert_manager.log_event(frame, event_type="MOTION_NO_FACE")

        time.sleep(0.04)  # ~25 fps processing cap


if __name__ == "__main__":
    main()

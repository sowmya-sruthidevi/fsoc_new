import random
import math

from PySide6.QtWidgets import QWidget, QMenuBar, QFileDialog
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QAction, QImage

from src.simulation.beacon import Beacon
from src.simulation.camera import VirtualCamera
from src.simulation.sky_environment import SkyEnvironment
from src.simulation.ocean_environment import OceanEnvironment
from src.tracking.controller import TrackingController

try:
    import cv2
except ImportError:
    cv2 = None


class Environment(QWidget):

    def __init__(self):

        super().__init__()

        self.setMinimumSize(1000, 650)
        self.setFocusPolicy(Qt.StrongFocus)

        # =================================
        # OPERATING MODE
        # =================================
        # VIRTUAL = current simulation. VIDEO and LIVE are reserved for
        # the next tracking-input stages and do not alter the current
        # virtual simulation implementation.
        self.operating_mode = "VIRTUAL"

        # =================================
        # HEADER MENU
        # =================================

        self.menu_bar = QMenuBar(self)
        self.menu_bar.setGeometry(0, 0, self.width(), 30)
        self.menu_bar.setStyleSheet("""
            QMenuBar {
                background-color: #181a1f;
                color: #d6d9df;
                padding-left: 8px;
                border-bottom: 1px solid #3a3a3a;
            }
            QMenuBar::item {
                background: transparent;
                padding: 6px 12px;
            }
            QMenuBar::item:selected {
                background-color: #2b3038;
            }
            QMenu {
                background-color: #181a1f;
                color: #d6d9df;
                border: 1px solid #3a4049;
            }
            QMenu::item {
                padding: 7px 28px 7px 18px;
            }
            QMenu::item:selected {
                background-color: #2b3038;
            }
        """)

        file_menu = self.menu_bar.addMenu("File")
        mode_menu = self.menu_bar.addMenu("Mode")
        simulation_menu = self.menu_bar.addMenu("Simulation")
        help_menu = self.menu_bar.addMenu("Help")

        # =================================
        # OPERATING MODE MENU
        # =================================

        virtual_mode_action = QAction("Virtual Simulation", self)
        virtual_mode_action.triggered.connect(
            lambda: self.set_operating_mode("VIRTUAL")
        )
        mode_menu.addAction(virtual_mode_action)

        video_upload_menu = mode_menu.addMenu("Video Upload")

        video_upload_action = QAction("Open Video File", self)
        video_upload_action.triggered.connect(self.open_video_file)
        video_upload_menu.addAction(video_upload_action)

        live_tracking_menu = mode_menu.addMenu("Live Tracking")

        live_mode_action = QAction("Start Live Camera", self)
        live_mode_action.triggered.connect(self.start_live_tracking)
        live_tracking_menu.addAction(live_mode_action)

        live_stop_action = QAction("Stop Live Camera", self)
        live_stop_action.triggered.connect(self.stop_live_tracking)
        live_tracking_menu.addAction(live_stop_action)

        reset_action = QAction("Reset", self)
        reset_action.triggered.connect(self.reset_simulation)
        file_menu.addAction(reset_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        space_action = QAction("Space Environment", self)
        space_action.triggered.connect(lambda: self.select_environment("SPACE"))
        simulation_menu.addAction(space_action)

        sky_action = QAction("Sky Environment", self)
        sky_action.triggered.connect(lambda: self.select_environment("SKY"))
        simulation_menu.addAction(sky_action)

        ocean_action = QAction("Ocean Environment", self)
        ocean_action.triggered.connect(lambda: self.select_environment("OCEAN"))
        simulation_menu.addAction(ocean_action)

        simulation_menu.addSeparator()

        pause_action = QAction("Pause / Resume", self)
        pause_action.triggered.connect(self.toggle_pause)
        simulation_menu.addAction(pause_action)

        simulation_menu.addSeparator()

        # =================================
        # DISTURBANCE MODE SUBMENU
        # =================================

        disturbance_menu = simulation_menu.addMenu("Disturbance Mode")

        camera_disturbance_action = QAction("Camera Disturbance", self)
        camera_disturbance_action.triggered.connect(
            lambda: self.set_disturbance_mode("CAMERA")
        )
        disturbance_menu.addAction(camera_disturbance_action)

        beacon_disturbance_action = QAction("Beacon Disturbance", self)
        beacon_disturbance_action.triggered.connect(
            lambda: self.set_disturbance_mode("BEACON")
        )
        disturbance_menu.addAction(beacon_disturbance_action)

        both_disturbance_action = QAction("Both Disturbance", self)
        both_disturbance_action.triggered.connect(
            lambda: self.set_disturbance_mode("BOTH")
        )
        disturbance_menu.addAction(both_disturbance_action)

        disturbance_menu.addSeparator()

        no_disturbance_action = QAction("No Disturbance", self)
        no_disturbance_action.triggered.connect(
            lambda: self.set_disturbance_mode("OFF")
        )
        disturbance_menu.addAction(no_disturbance_action)

        disturbance_menu.addSeparator()

        strength_menu = disturbance_menu.addMenu("Disturbance Strength")

        low_strength_action = QAction("Low", self)
        low_strength_action.triggered.connect(
            lambda: self.set_disturbance_strength("LOW")
        )
        strength_menu.addAction(low_strength_action)

        medium_strength_action = QAction("Medium", self)
        medium_strength_action.triggered.connect(
            lambda: self.set_disturbance_strength("MEDIUM")
        )
        strength_menu.addAction(medium_strength_action)

        high_strength_action = QAction("High", self)
        high_strength_action.triggered.connect(
            lambda: self.set_disturbance_strength("HIGH")
        )
        strength_menu.addAction(high_strength_action)

        controls_action = QAction("Keyboard Controls", self)
        controls_action.triggered.connect(self.show_controls)
        help_menu.addAction(controls_action)

        # =================================
        # CURRENT ENVIRONMENT
        # =================================

        self.current_environment = "SPACE"

        # =================================
        # ENVIRONMENTS
        # =================================

        self.sky_environment = SkyEnvironment()
        self.ocean_environment = OceanEnvironment()

        # =================================
        # SPACE STARS
        # =================================

        self.stars = []

        for _ in range(180):

            self.stars.append({

                "x": random.randint(0, 1400),
                "y": random.randint(0, 900),

                "size": random.uniform(1, 3),

                "phase": random.uniform(
                    0,
                    math.pi * 2
                ),

                "speed": random.uniform(
                    0.02,
                    0.08
                )
            })

        # =================================
        # ANIMATION
        # =================================

        self.animation_time = 0.0

        # =================================
        # SKY SUN MOVEMENT
        # =================================

        self.sky_sun_progress = 0.08
        self.sky_sun_speed = 0.00025

        # =================================
        # SUN OCCLUSION
        # =================================

        self.sun_occluded = False
        self.previous_sun_occluded = False

        # =================================
        # TARGET
        # =================================

        self.beacon = Beacon(
            x=300,
            y=200
        )

        # =================================
        # CAMERA
        # =================================

        self.camera = VirtualCamera(
            x=125,
            y=75,
            width=250,
            height=180
        )

        # =================================
        # CONTROLLER
        # =================================

        self.controller = TrackingController()

        # =================================
        # TARGET VISIBILITY
        # =================================

        self.target_visible = False
        self.previous_visible = False

        # =================================
        # STATE
        # =================================

        self.state = "SEARCHING"
        self.state_counter = 0

        # =================================
        # TRACKING ERROR
        # =================================

        self.error_x = 0.0
        self.error_y = 0.0

        # =================================
        # GENERAL METRICS
        # =================================

        self.confidence = 0.0
        self.lock_status = "NOT LOCKED"

        # =================================
        # LOCK THRESHOLD
        # =================================

        # =================================
         # LOCK SETTINGS
       # =================================

       # Target must be close to center
        self.lock_threshold = 15.0

        # Number of frames required
        # before final lock
        self.lock_required_frames = 25

        # Current stable tracking frames
        self.lock_counter = 0

        # =================================
        # GRAPH METRIC HISTORY
        # =================================

        self.max_graph_points = 100
        self.confidence_history = []
        self.error_x_history = []
        self.error_y_history = []

        # =================================
        # RUNNING
        # =================================

        self.is_running = True

        # =================================
        # STARTUP STABILIZATION
        # =================================
        # Give the virtual camera a short settling period when the
        # application first opens. This prevents the camera from jumping
        # around while the first tracking frames are being initialized.
        self.startup_frames = 90
        self.startup_complete = False

        # =================================
        # DISTURBANCE MODEL
        # =================================

        # Simulates platform vibration, slow drift, and small random
        # pointing disturbances that make FSOC tracking more realistic.
        # Disturbance test modes:
        # CAMERA = camera moves, beacon stays fixed
        # BEACON = beacon moves, camera stays fixed
        # BOTH   = camera and beacon move independently
        # OFF    = normal simulation/tracking
        self.disturbance_mode = "OFF"
        self.disturbances_enabled = False

        # Strong enough to be clearly visible in the simulation.
        self.disturbance_strength = 1.5
        self.disturbance_strength_name = "MEDIUM"

        # =================================
        # DISTURBANCE PERFORMANCE METRICS
        # =================================

        self.disturbance_peak_error = 0.0
        self.disturbance_event_count = 0
        self.disturbance_event_active = False

        # Fixed target position used by camera-disturbance tests.
        self.disturbance_beacon_x = self.beacon.x
        self.disturbance_beacon_y = self.beacon.y

        # =================================
        # VIDEO TRACKING
        # =================================

        self.video_capture = None
        self.video_path = ""
        self.video_frame = None
        self.video_frame_rgb = None
        self.video_frame_width = 0
        self.video_frame_height = 0
        self.video_target_found = False
        self.video_target_x = 0.0
        self.video_target_y = 0.0
        self.video_error_x = 0.0
        self.video_error_y = 0.0
        self.video_confidence = 0.0
        self.video_lock_counter = 0
        self.video_lock = False

        # Virtual camera for uploaded-video tracking.
        # A recorded camera cannot physically move, so we simulate
        # camera motion by moving a crop/viewport toward the beacon.
        self.video_camera_x = 0.0
        self.video_camera_y = 0.0
        self.video_crop_ratio = 0.42
        self.video_camera_gain = 0.34
        self.video_target_smooth_x = None
        self.video_target_smooth_y = None
        self.video_last_seen_x = None
        self.video_last_seen_y = None
        self.video_missing_frames = 0

        # Video tracking performance history.
        self.video_confidence_history = []
        self.video_error_x_history = []
        self.video_error_y_history = []

        # =================================
        # LIVE CAMERA TRACKING
        # =================================
        self.live_capture = None
        self.live_frame = None
        self.live_frame_rgb = None
        self.live_frame_width = 0
        self.live_frame_height = 0
        self.live_target_found = False
        self.live_target_x = 0.0
        self.live_target_y = 0.0
        self.live_error_x = 0.0
        self.live_error_y = 0.0
        self.live_confidence = 0.0
        self.live_lock_counter = 0
        self.live_lock = False
        self.live_target_smooth_x = None
        self.live_target_smooth_y = None
        self.live_last_seen_x = None
        self.live_last_seen_y = None
        self.live_missing_frames = 0

        # Live tracking performance history.
        self.live_confidence_history = []
        self.live_error_x_history = []
        self.live_error_y_history = []

        # Virtual camera viewport for live tracking.
        # The physical webcam cannot pan programmatically, so the UI
        # simulates pan/tilt by moving a crop over the live frame.
        self.live_camera_x = 0.0
        self.live_camera_y = 0.0
        self.live_crop_ratio = 0.26
        self.live_camera_gain = 0.62

        # =================================
        # TIMER
        # =================================

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_simulation
        )

        self.timer.start(16)


    # =================================
    # UPDATE SIMULATION
    # =================================

    # =================================
    # MENU ACTIONS
    # =================================

    def set_operating_mode(self, mode):
        if mode != "VIDEO" and self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        if mode != "LIVE" and self.live_capture is not None:
            self.live_capture.release()
            self.live_capture = None

        self.operating_mode = mode

        if mode == "VIRTUAL":
            self.is_running = True
        elif mode == "VIDEO":
            self.is_running = False
            self.state = "VIDEO TRACKING"
            self.target_visible = False
            self.lock_status = "NOT LOCKED"
            self.confidence = 0.0
            self.error_x = 0.0
            self.error_y = 0.0
        else:
            self.is_running = False
            self.state = "LIVE TRACKING"
            self.target_visible = False
            self.lock_status = "NOT LOCKED"
            self.confidence = 0.0
            self.error_x = 0.0
            self.error_y = 0.0

        self.setFocus()
        self.update()

    def open_video_file(self):
        if cv2 is None:
            self.video_path = "OpenCV is not installed"
            self.update()
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Beacon Tracking Video",
            "",
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv);;All Files (*)"
        )
        if not path:
            return

        if self.video_capture is not None:
            self.video_capture.release()

        self.video_capture = cv2.VideoCapture(path)
        if not self.video_capture.isOpened():
            self.video_capture = None
            self.video_path = "Unable to open video"
            self.update()
            return

        self.video_path = path
        self.operating_mode = "VIDEO"
        self.is_running = True
        self.video_target_found = False
        self.video_lock_counter = 0
        self.video_lock = False
        self.video_target_smooth_x = None
        self.video_target_smooth_y = None
        self.video_last_seen_x = None
        self.video_last_seen_y = None
        self.video_missing_frames = 0
        self.video_confidence_history.clear()
        self.video_error_x_history.clear()
        self.video_error_y_history.clear()

        # Start the virtual camera at the uploaded video's center.
        self.video_camera_x = self.video_frame_width / 2.0 if self.video_frame_width else 0.0
        self.video_camera_y = self.video_frame_height / 2.0 if self.video_frame_height else 0.0

        self.state = "VIDEO TRACKING"
        self.update()

    def start_live_tracking(self):
        if cv2 is None:
            self.operating_mode = "LIVE"
            self.live_capture = None
            self.state = "OPENING CAMERA"
            self.update()
            return

        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        if self.live_capture is not None:
            self.live_capture.release()

        self.live_capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.live_capture.isOpened():
            self.live_capture.release()
            self.live_capture = None
            self.operating_mode = "LIVE"
            self.state = "CAMERA ERROR"
            self.update()
            return

        self.operating_mode = "LIVE"
        self.is_running = True
        self.live_target_found = False
        self.live_lock_counter = 0
        self.live_lock = False
        self.live_target_smooth_x = None
        self.live_target_smooth_y = None
        self.live_last_seen_x = None
        self.live_last_seen_y = None
        self.live_missing_frames = 0
        self.live_confidence_history.clear()
        self.live_error_x_history.clear()
        self.live_error_y_history.clear()
        self.live_camera_x = 0.0
        self.live_camera_y = 0.0
        self.state = "SEARCHING"
        self.update()

    def stop_live_tracking(self):
        if self.live_capture is not None:
            self.live_capture.release()
            self.live_capture = None
        self.live_frame = None
        self.live_frame_rgb = None
        self.live_confidence_history.clear()
        self.live_error_x_history.clear()
        self.live_error_y_history.clear()
        self.operating_mode = "LIVE"
        self.is_running = False
        self.live_target_found = False
        self.live_lock = False
        self.live_lock_counter = 0
        self.state = "LIVE CAMERA STOPPED"
        self.update()

    def update_live_frame(self):
        if self.live_capture is None:
            return

        ok, frame = self.live_capture.read()
        if not ok:
            self.live_missing_frames += 1
            return

        self.live_frame = frame
        self.live_frame_height, self.live_frame_width = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.live_frame_rgb = QImage(
            rgb.data, self.live_frame_width, self.live_frame_height,
            self.live_frame_width * 3, QImage.Format_RGB888
        ).copy()

        # -------------------------------------------------------------
        # BEACON DETECTION
        # Detect a compact, saturated optical point rather than general
        # bright areas such as faces, walls or reflections.
        # -------------------------------------------------------------
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3, 3), 0)

        # Use a very high threshold for an optical beacon.  A second
        # adaptive threshold catches slightly dimmer frames without
        # allowing ordinary room lighting to dominate.
        peak_gray = float(gray.max())
        threshold_value = 250 if peak_gray >= 252 else 245
        _, thresh = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        best = None
        best_score = -1.0
        frame_area = float(max(1, self.live_frame_width * self.live_frame_height))
        ref_x, ref_y = self.live_last_seen_x, self.live_last_seen_y

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 1.0 or area > frame_area * 0.025:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            if w < 1 or h < 1:
                continue
            if w > self.live_frame_width * 0.12 or h > self.live_frame_height * 0.12:
                continue

            roi_gray = gray[y:y+h, x:x+w]
            roi_bgr = frame[y:y+h, x:x+w]
            if roi_gray.size == 0 or roi_bgr.size == 0:
                continue

            peak = float(roi_gray.max())
            mean_brightness = float(roi_gray.mean())
            min_channel = float(roi_bgr.min(axis=2).mean())
            max_channel = float(roi_bgr.max(axis=2).mean())
            white_ratio = min_channel / max(1.0, max_channel)

            # A real optical beacon is usually a small, intense white
            # source. Reject candidates that are large/soft or strongly
            # colored.
            compactness = area / max(1.0, float(w * h))
            perimeter = cv2.arcLength(contour, True)
            circularity = (4.0 * math.pi * area / (perimeter * perimeter)) if perimeter > 0 else 0.0

            if peak < 245 or white_ratio < 0.68:
                continue

            # Estimate local contrast against a small surrounding ring.
            pad = max(3, int(max(w, h) * 2))
            x0, y0 = max(0, x - pad), max(0, y - pad)
            x1 = min(self.live_frame_width, x + w + pad)
            y1 = min(self.live_frame_height, y + h + pad)
            surround = gray[y0:y1, x0:x1]
            local_mean = float(surround.mean()) if surround.size else 0.0
            contrast = max(0.0, peak - local_mean)

            score = (
                peak * 0.35
                + min(255.0, contrast) * 0.35
                + min(255.0, mean_brightness) * 0.10
                + white_ratio * 100.0 * 0.10
                + min(1.0, compactness * 2.0) * 100.0 * 0.05
                + min(1.0, circularity * 2.0) * 100.0 * 0.05
            )

            if ref_x is not None and ref_y is not None:
                cx0, cy0 = x + w / 2.0, y + h / 2.0
                jump = math.hypot(cx0 - ref_x, cy0 - ref_y)
                max_jump = max(55.0, min(self.live_frame_width, self.live_frame_height) * 0.28)
                proximity = math.exp(-jump / max_jump)
                score *= 0.18 + 0.82 * proximity

            if score > best_score:
                best_score = score
                best = (x, y, w, h, area, contrast, white_ratio)

        self.live_target_found = best is not None

        if best is not None:
            x, y, w, h, area, beacon_contrast, beacon_white_ratio = best
            raw_x = x + w / 2.0
            raw_y = y + h / 2.0

            if self.live_target_smooth_x is None:
                self.live_target_smooth_x = raw_x
                self.live_target_smooth_y = raw_y
            else:
                alpha = 0.55
                self.live_target_smooth_x += alpha * (raw_x - self.live_target_smooth_x)
                self.live_target_smooth_y += alpha * (raw_y - self.live_target_smooth_y)

            self.live_target_x = self.live_target_smooth_x
            self.live_target_y = self.live_target_smooth_y
            self.live_last_seen_x = self.live_target_x
            self.live_last_seen_y = self.live_target_y
            self.live_missing_frames = 0

            # Start the virtual pan/tilt camera at the real frame center.
            if self.live_camera_x == 0.0 and self.live_camera_y == 0.0:
                self.live_camera_x = self.live_frame_width / 2.0
                self.live_camera_y = self.live_frame_height / 2.0

            # Smaller crop makes the camera motion visibly demonstrable.
            crop_w = self.live_frame_width * self.live_crop_ratio
            crop_h = self.live_frame_height * self.live_crop_ratio
            half_w = crop_w / 2.0
            half_h = crop_h / 2.0

            # ---------------------------------------------------------
            # CLOSED-LOOP VIRTUAL CAMERA
            # The camera center moves toward the detected beacon.
            # ---------------------------------------------------------
            self.live_error_x = self.live_target_x - self.live_camera_x
            self.live_error_y = self.live_target_y - self.live_camera_y

            move_x = self.live_error_x * self.live_camera_gain
            move_y = self.live_error_y * self.live_camera_gain
            max_step = max(6.0, min(self.live_frame_width, self.live_frame_height) * 0.045)
            move_x = max(-max_step, min(max_step, move_x))
            move_y = max(-max_step, min(max_step, move_y))

            self.live_camera_x += move_x
            self.live_camera_y += move_y

            self.live_camera_x = max(half_w, min(self.live_frame_width - half_w, self.live_camera_x))
            self.live_camera_y = max(half_h, min(self.live_frame_height - half_h, self.live_camera_y))

            self.live_error_x = self.live_target_x - self.live_camera_x
            self.live_error_y = self.live_target_y - self.live_camera_y
            distance = math.hypot(self.live_error_x, self.live_error_y)

            # Confidence combines beacon quality and alignment.
            area_conf = min(1.0, area / max(3.0, frame_area * 0.00035))
            contrast_conf = min(1.0, beacon_contrast / 180.0)
            whiteness_conf = min(1.0, beacon_white_ratio / 0.90)
            beacon_quality = 0.45 * area_conf + 0.35 * contrast_conf + 0.20 * whiteness_conf
            center_distance = math.hypot(
                self.live_target_x - self.live_camera_x,
                self.live_target_y - self.live_camera_y
            )
            max_distance = math.hypot(
                self.live_frame_width / 2.0, self.live_frame_height / 2.0
            )
            center_conf = max(0.0, 1.0 - center_distance / max(1.0, max_distance))
            self.live_confidence = max(0.0, min(100.0,
                (0.70 * beacon_quality + 0.30 * center_conf) * 100.0
            ))

            if distance <= 22.0:
                self.live_lock_counter += 1
            else:
                self.live_lock_counter = max(0, self.live_lock_counter - 2)

            self.live_lock = self.live_lock_counter >= 10
            self.state = "LOCKED" if self.live_lock else "TRACKING"

        else:
            self.live_missing_frames += 1
            if self.live_last_seen_x is not None and self.live_missing_frames <= 8:
                self.live_target_x = self.live_last_seen_x
                self.live_target_y = self.live_last_seen_y
                self.live_error_x = self.live_target_x - self.live_camera_x
                self.live_error_y = self.live_target_y - self.live_camera_y

                # Continue the virtual camera motion for a few missed
                # frames instead of freezing the viewport.
                move_x = self.live_error_x * self.live_camera_gain * 0.55
                move_y = self.live_error_y * self.live_camera_gain * 0.55
                max_step = max(5.0, min(self.live_frame_width, self.live_frame_height) * 0.055)
                move_x = max(-max_step, min(max_step, move_x))
                move_y = max(-max_step, min(max_step, move_y))
                crop_w = self.live_frame_width * self.live_crop_ratio
                crop_h = self.live_frame_height * self.live_crop_ratio
                half_w = crop_w / 2.0
                half_h = crop_h / 2.0
                self.live_camera_x += move_x
                self.live_camera_y += move_y
                self.live_camera_x = max(half_w, min(self.live_frame_width - half_w, self.live_camera_x))
                self.live_camera_y = max(half_h, min(self.live_frame_height - half_h, self.live_camera_y))
                self.live_confidence = max(0.0, self.live_confidence - 1.0)
                self.state = "TRACKING"
            else:
                self.live_lock_counter = 0
                self.live_lock = False
                self.live_confidence = max(0.0, self.live_confidence - 4.0)
                self.live_error_x = 0.0
                self.live_error_y = 0.0
                self.state = "SEARCHING"

        self.live_confidence_history.append(self.live_confidence)
        self.live_error_x_history.append(self.live_error_x)
        self.live_error_y_history.append(self.live_error_y)
        if len(self.live_confidence_history) > self.max_graph_points:
            self.live_confidence_history.pop(0)
        if len(self.live_error_x_history) > self.max_graph_points:
            self.live_error_x_history.pop(0)
        if len(self.live_error_y_history) > self.max_graph_points:
            self.live_error_y_history.pop(0)

        self.update()

    def update_video_frame(self):
        if self.video_capture is None:
            return

        ok, frame = self.video_capture.read()
        if not ok:
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self.video_capture.read()
            if not ok:
                return

        self.video_frame = frame
        self.video_frame_height, self.video_frame_width = frame.shape[:2]

        # Keep the virtual camera inside the video frame.
        crop_w = max(1.0, self.video_frame_width * self.video_crop_ratio)
        crop_h = max(1.0, self.video_frame_height * self.video_crop_ratio)
        half_w = crop_w / 2.0
        half_h = crop_h / 2.0
        if self.video_camera_x <= 0.0 and self.video_camera_y <= 0.0:
            self.video_camera_x = self.video_frame_width / 2.0
            self.video_camera_y = self.video_frame_height / 2.0
        self.video_camera_x = max(half_w, min(self.video_camera_x, self.video_frame_width - half_w))
        self.video_camera_y = max(half_h, min(self.video_camera_y, self.video_frame_height - half_h))

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.video_frame_rgb = QImage(
            rgb.data,
            self.video_frame_width,
            self.video_frame_height,
            self.video_frame_width * 3,
            QImage.Format_RGB888
        ).copy()

        # Generic beacon detector: find the brightest compact region.
        # This works well for a visible/bright optical beacon without
        # requiring a trained model for the first video-input stage.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (7, 7), 0)
        _, threshold = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(
            threshold, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        best = None
        best_score = -1.0
        frame_area = float(max(1, self.video_frame_width * self.video_frame_height))

        # Once the beacon has been acquired, prefer bright candidates near
        # the previous beacon position. This prevents a bright wall/phone
        # reflection from stealing the tracker after a few frames.
        reference_x = self.video_last_seen_x
        reference_y = self.video_last_seen_y

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 3 or area > frame_area * 0.05:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w > self.video_frame_width * 0.35 or h > self.video_frame_height * 0.35:
                continue

            cx = x + w / 2.0
            cy = y + h / 2.0
            brightness = float(gray[y:y+h, x:x+w].mean())
            base_score = area * brightness

            if reference_x is not None and reference_y is not None:
                jump = math.hypot(cx - reference_x, cy - reference_y)
                # Strongly penalize implausibly large frame-to-frame jumps.
                motion_score = math.exp(-jump / max(30.0, min(self.video_frame_width, self.video_frame_height) * 0.18))
                score = base_score * (0.35 + 0.65 * motion_score)
            else:
                score = base_score

            if score > best_score:
                best_score = score
                best = (x, y, w, h, area)

        self.video_target_found = best is not None

        if best is not None:
            x, y, w, h, area = best
            raw_x = x + w / 2.0
            raw_y = y + h / 2.0

            # Smooth the detected beacon position so the virtual camera
            # follows continuously instead of jumping between frames.
            if self.video_target_smooth_x is None:
                self.video_target_smooth_x = raw_x
                self.video_target_smooth_y = raw_y
            else:
                alpha = 0.42
                self.video_target_smooth_x += alpha * (raw_x - self.video_target_smooth_x)
                self.video_target_smooth_y += alpha * (raw_y - self.video_target_smooth_y)

            self.video_target_x = self.video_target_smooth_x
            self.video_target_y = self.video_target_smooth_y
            self.video_last_seen_x = self.video_target_x
            self.video_last_seen_y = self.video_target_y
            self.video_missing_frames = 0

            # Error is measured against the MOVING virtual camera center,
            # not the fixed center of the original video frame.
            self.video_error_x = self.video_target_x - self.video_camera_x
            self.video_error_y = self.video_target_y - self.video_camera_y

            # Virtual camera control: pan the displayed viewport toward the
            # detected beacon. This is the video equivalent of camera motion
            # in the Virtual Simulation mode.
            move_x = self.video_error_x * self.video_camera_gain
            move_y = self.video_error_y * self.video_camera_gain
            self.video_camera_x += move_x
            self.video_camera_y += move_y

            self.video_camera_x = max(half_w, min(self.video_camera_x, self.video_frame_width - half_w))
            self.video_camera_y = max(half_h, min(self.video_camera_y, self.video_frame_height - half_h))

            # Recalculate the residual pointing error after the camera move.
            self.video_error_x = self.video_target_x - self.video_camera_x
            self.video_error_y = self.video_target_y - self.video_camera_y

            area_conf = min(1.0, area / max(20.0, frame_area * 0.002))
            distance = math.hypot(self.video_error_x, self.video_error_y)
            max_distance = math.hypot(self.video_frame_width / 2.0, self.video_frame_height / 2.0)
            center_conf = max(0.0, 1.0 - distance / max(1.0, max_distance))
            self.video_confidence = max(0.0, min(100.0, (0.55 * area_conf + 0.45 * center_conf) * 100.0))

            if distance <= 25.0:
                self.video_lock_counter += 1
            else:
                self.video_lock_counter = max(0, self.video_lock_counter - 2)

            self.video_lock = self.video_lock_counter >= 8
            self.state = "LOCKED" if self.video_lock else "TRACKING"
            self.lock_status = "LOCKED" if self.video_lock else "NOT LOCKED"
        else:
            # Do not immediately lose the target because of one bad frame.
            # Hold the last valid target briefly while the detector recovers.
            self.video_missing_frames += 1
            if self.video_last_seen_x is not None and self.video_missing_frames <= 6:
                self.video_target_x = self.video_last_seen_x
                self.video_target_y = self.video_last_seen_y
                self.video_error_x = self.video_target_x - self.video_camera_x
                self.video_error_y = self.video_target_y - self.video_camera_y
                self.video_confidence = max(0.0, self.video_confidence - 1.5)
                self.state = "TRACKING"
            else:
                self.video_confidence = max(0.0, self.video_confidence - 5.0)
                self.video_lock_counter = 0
                self.video_lock = False
                self.state = "SEARCHING"
                self.lock_status = "NOT LOCKED"
                self.video_error_x = 0.0
                self.video_error_y = 0.0

        # Keep a rolling history for the Video Upload performance graphs.
        self.video_confidence_history.append(self.video_confidence)
        self.video_error_x_history.append(self.video_error_x)
        self.video_error_y_history.append(self.video_error_y)
        if len(self.video_confidence_history) > self.max_graph_points:
            self.video_confidence_history.pop(0)
        if len(self.video_error_x_history) > self.max_graph_points:
            self.video_error_x_history.pop(0)
        if len(self.video_error_y_history) > self.max_graph_points:
            self.video_error_y_history.pop(0)

        self.update()

    def select_environment(self, environment):
        self.current_environment = environment
        self.sun_occluded = False
        self.previous_sun_occluded = False
        self.update()

    def toggle_pause(self):
        self.is_running = not self.is_running
        self.setFocus()

    def set_disturbance_mode(self, mode):
        self.disturbance_mode = mode
        self.disturbances_enabled = (mode != "OFF")

        # Capture the current target when entering CAMERA mode so the
        # beacon remains fixed while the camera is disturbed.
        if mode == "CAMERA":
            self.disturbance_beacon_x = self.beacon.x
            self.disturbance_beacon_y = self.beacon.y

        self.setFocus()
        self.update()

    def set_disturbance_strength(self, strength):
        strength_values = {
            "LOW": 0.6,
            "MEDIUM": 1.5,
            "HIGH": 3.0
        }

        self.disturbance_strength_name = strength
        self.disturbance_strength = strength_values.get(
            strength,
            1.5
        )

        self.setFocus()
        self.update()


    def toggle_disturbances(self):
        # Keep the old D shortcut working.
        if self.disturbances_enabled:
            self.set_disturbance_mode("OFF")
        else:
            self.set_disturbance_mode("CAMERA")


    def reset_simulation(self):
        self.beacon.x = 300
        self.beacon.y = 200
        self.beacon.vx = 2.5
        self.beacon.vy = 1.8

        self.sky_sun_progress = 0.08
        self.sun_occluded = False
        self.previous_sun_occluded = False

        self.camera.x = 250
        self.camera.y = 150

        if hasattr(self.camera, "search_direction"):
            self.camera.search_direction = 1
        if hasattr(self.camera, "search_vertical_direction"):
            self.camera.search_vertical_direction = 1

        self.state = "SEARCHING"
        self.target_visible = False
        self.previous_visible = False
        self.error_x = 0.0
        self.error_y = 0.0
        self.confidence = 0.0
        self.lock_status = "NOT LOCKED"
        self.state_counter = 0
        self.lock_counter = 0
        self.disturbance_mode = "OFF"
        self.disturbances_enabled = False
        self.disturbance_strength = 1.5
        self.disturbance_strength_name = "MEDIUM"
        self.disturbance_peak_error = 0.0
        self.disturbance_event_count = 0
        self.disturbance_event_active = False
        self.disturbance_beacon_x = self.beacon.x
        self.disturbance_beacon_y = self.beacon.y

        self.confidence_history.clear()
        self.error_x_history.clear()
        self.error_y_history.clear()

        self.is_running = (self.operating_mode == "VIRTUAL")
        self.setFocus()
        self.update()

    def show_controls(self):
        # Controls are intentionally kept in the header menu/shortcuts.
        self.setFocus()
        self.update()

    def resizeEvent(self, event):
        self.menu_bar.setGeometry(0, 0, self.width(), 30)
        super().resizeEvent(event)

    def update_simulation(self):

        if self.operating_mode == "VIDEO":
            if self.is_running:
                self.update_video_frame()
            else:
                self.update()
            return

        if self.operating_mode == "LIVE":
            if self.is_running and self.live_capture is not None:
                self.update_live_frame()
            else:
                self.update()
            return

        # Animation

        self.animation_time += 0.05

        # =================================
        # STARTUP STABILIZATION
        # =================================
        if not self.startup_complete:
            self.startup_frames -= 1

            # Keep the camera initially centered on the beacon so the
            # simulation opens in a stable, immediately understandable
            # tracking position.
            target_cx = self.beacon.x - self.camera.width / 2.0
            target_cy = self.beacon.y - self.camera.height / 2.0
            self.camera.x += (target_cx - self.camera.x) * 0.18
            self.camera.y += (target_cy - self.camera.y) * 0.18

            if self.startup_frames <= 0:
                self.startup_complete = True
                self.lock_counter = 0
                self.state = "TRACKING"

                # IMPORTANT: startup always remains disturbance-free.
                # Disturbances begin only after the user explicitly
                # selects Camera, Beacon, or Both from the menu.
                self.disturbance_mode = "OFF"
                self.disturbances_enabled = False

        # =================================
        # UPDATE ENVIRONMENTS
        # =================================

        if self.current_environment == "SKY":

            self.sky_environment.update(
                self.width()
            )

        elif self.current_environment == "OCEAN":

            self.ocean_environment.update(
                self.width()
            )

        # =================================
        # PAUSE
        # =================================

        if not self.is_running:

            self.update()
            return

        # =================================
        # MOVE TARGET
        # =================================

        if self.current_environment == "SPACE":

            if self.disturbance_mode in ("CAMERA", "BOTH"):
                # In CAMERA mode the beacon is deliberately fixed.
                # In BOTH mode its own disturbance is applied below.
                if self.disturbance_mode == "CAMERA":
                    self.beacon.x = self.disturbance_beacon_x
                    self.beacon.y = self.disturbance_beacon_y
            else:
                self.beacon.update(
                    self.width(),
                    self.height()
                )

            self.sun_occluded = False


        elif self.current_environment == "SKY":

            # Move sun slowly

            self.sky_sun_progress += (
                self.sky_sun_speed
            )

            # Restart sun path

            if self.sky_sun_progress >= 1.0:

                self.sky_sun_progress = 0.0

                self.state = "SEARCHING"

                self.target_visible = False
                self.previous_visible = False

                self.sun_occluded = False
                self.previous_sun_occluded = False

            # =================================
            # SUN HORIZONTAL PATH
            # =================================

            start_x = -self.beacon.radius

            end_x = (
                self.width()
                +
                self.beacon.radius
            )

            self.beacon.x = (

                start_x

                +

                (
                    end_x - start_x
                )

                *

                self.sky_sun_progress

            )

            # =================================
            # SUN ARC PATH
            # =================================

            horizon_y = (
                self.height() * 0.38
            )

            sky_arc_height = (
                self.height() * 0.22
            )

            sun_arc = (

                math.sin(

                    math.pi
                    *
                    self.sky_sun_progress

                )

                *

                sky_arc_height

            )

            self.beacon.y = (

                horizon_y
                -
                sun_arc

            )

            # =================================
            # CHECK CLOUD OCCLUSION
            # =================================

            self.sun_occluded = (

                self.sky_environment.check_sun_occlusion(

                    self.beacon.x,

                    self.beacon.y,

                    sun_radius=25

                )

            )


        elif self.current_environment == "OCEAN":

            if self.disturbance_mode in ("CAMERA", "BOTH"):
                if self.disturbance_mode == "CAMERA":
                    self.beacon.x = self.disturbance_beacon_x
                    self.beacon.y = self.disturbance_beacon_y
            else:
                self.beacon.update(
                    self.width(),
                    self.height()
                )

            self.sun_occluded = False

        # =================================
        # CAMERA VISIBILITY
        # =================================

        camera_can_see_target = (

            self.camera.is_target_visible(

                self.beacon.x,

                self.beacon.y

            )

        )

        # =================================
        # FINAL TARGET VISIBILITY
        # =================================

        if (

            self.current_environment == "SKY"

            and

            self.sun_occluded

        ):

            self.target_visible = False

        else:

            self.target_visible = (
                camera_can_see_target
            )

        # =================================
        # OCCLUDED STATE
        # =================================

        if (

            self.current_environment == "SKY"

            and

            self.sun_occluded

        ):

            self.state = "OCCLUDED"

            self.state_counter = 0

        else:

            # =================================
            # TARGET ACQUIRED
            # =================================

            if (

                self.target_visible

                and

                not self.previous_visible

            ):

                self.state = "ACQUIRED"

                self.state_counter = 60

            # =================================
            # TARGET LOST
            # =================================

            elif (

                not self.target_visible

                and

                self.previous_visible

            ):

                self.state = "LOST"

                self.state_counter = 60

        # =================================
        # CAMERA BEHAVIOR
        # =================================

        if self.target_visible and self.startup_complete:

            # Calculate error

            self.error_x, self.error_y = (

                self.camera.calculate_error(

                    self.beacon.x,

                    self.beacon.y

                )

            )

            # In BEACON/BOTH disturbance test modes the camera is held
            # stable so the disturbance itself can be observed clearly.
            if self.disturbance_mode not in ("BEACON", "BOTH"):

                # Controller movement

                move_x, move_y = (

                    self.controller.calculate_movement(

                        self.error_x,

                        self.error_y

                    )

                )

                # Move camera

                self.camera.move(

                    move_x,

                    move_y,

                    self.width(),

                    self.height()

                )

        elif self.startup_complete:

            # Search only after startup stabilization.
            if self.state != "OCCLUDED":
                self.camera.search(
                    self.width(),
                    self.height()
                )

        # =================================
        # APPLY SELECTED DISTURBANCE
        # =================================

        if self.disturbances_enabled and self.startup_complete:

            # Smooth platform drift + vibration + random jitter.
            camera_dx = (
                math.sin(self.animation_time * 0.75) * 1.6
                + math.sin(self.animation_time * 0.31) * 0.9
                + math.sin(self.animation_time * 7.0) * 2.8
                + math.sin(self.animation_time * 13.0) * 1.4
                + random.uniform(-1.8, 1.8)
            ) * self.disturbance_strength

            camera_dy = (
                math.sin(self.animation_time * 0.58 + 1.2) * 1.4
                + math.sin(self.animation_time * 0.27) * 0.7
                + math.sin(self.animation_time * 8.5 + 0.8) * 2.4
                + math.sin(self.animation_time * 15.0) * 1.2
                + random.uniform(-1.6, 1.6)
            ) * self.disturbance_strength

            # Independent beacon disturbance uses different frequencies
            # and random components, so camera and beacon do not move
            # in the same pattern.
            beacon_dx = (
                math.sin(self.animation_time * 0.43 + 2.0) * 2.0
                + math.sin(self.animation_time * 5.5) * 2.6
                + random.uniform(-1.5, 1.5)
            ) * self.disturbance_strength

            beacon_dy = (
                math.sin(self.animation_time * 0.37 + 0.7) * 1.8
                + math.sin(self.animation_time * 6.7 + 1.5) * 2.2
                + random.uniform(-1.4, 1.4)
            ) * self.disturbance_strength

            if self.disturbance_mode in ("CAMERA", "BOTH"):
                self.camera.x += camera_dx
                self.camera.y += camera_dy

            if self.disturbance_mode in ("BEACON", "BOTH"):
                # Start from the current target and apply an independent
                # disturbance every frame. Clamp it to the world.
                self.beacon.x += beacon_dx
                self.beacon.y += beacon_dy

            # Keep camera inside the simulation world.
            max_x = max(0, self.width() - self.camera.width)
            max_y = max(0, self.height() - self.camera.height)

            self.camera.x = max(0, min(self.camera.x, max_x))
            self.camera.y = max(0, min(self.camera.y, max_y))

            # Keep beacon inside the simulation world.
            radius = getattr(self.beacon, "radius", 10)
            self.beacon.x = max(radius, min(self.beacon.x, self.width() - radius))
            self.beacon.y = max(radius, min(self.beacon.y, self.height() - radius))

        # =================================
        # RECALCULATE ERROR
        # =================================

        self.error_x, self.error_y = (

            self.camera.calculate_error(

                self.beacon.x,

                self.beacon.y

            )

        )

        # =================================
        # CALCULATE CONFIDENCE
        # =================================

        distance_error = math.sqrt(

            self.error_x ** 2

            +

            self.error_y ** 2

        )

        max_error = math.sqrt(

            self.width() ** 2

            +

            self.height() ** 2

        )

        if self.target_visible:

            self.confidence = max(

                0.0,

                min(

                    100.0,

                    100.0 - (

                        distance_error
                        /
                        max_error
                        *
                        100

                    )

                )

            )

        else:

            self.confidence = 0.0

        # =================================
        # DISTURBANCE PERFORMANCE METRICS
        # =================================

        if self.disturbances_enabled:

            self.disturbance_peak_error = max(
                self.disturbance_peak_error,
                distance_error
            )

            disturbance_trigger = self.lock_threshold * 2.0

            if distance_error > disturbance_trigger:

                if not self.disturbance_event_active:
                    self.disturbance_event_count += 1
                    self.disturbance_event_active = True

            elif distance_error <= self.lock_threshold:

                self.disturbance_event_active = False

        # =================================
        # UPDATE GRAPH HISTORY
        # =================================

        self.confidence_history.append(self.confidence)
        self.error_x_history.append(self.error_x)
        self.error_y_history.append(self.error_y)

        if len(self.confidence_history) > self.max_graph_points:
            self.confidence_history.pop(0)

        if len(self.error_x_history) > self.max_graph_points:
            self.error_x_history.pop(0)

        if len(self.error_y_history) > self.max_graph_points:
            self.error_y_history.pop(0)

        # =================================
        # LOCK STATUS
        # =================================

        if self.state == "LOCKED":

          self.lock_status = "LOCKED"

        elif self.state == "LOCKING":

          self.lock_status = "LOCKING..."

        else:

           self.lock_status = "NOT LOCKED"
        # =================================
        # UPDATE NORMAL STATE
        # =================================

        if self.state != "OCCLUDED":

            if self.state_counter > 0:

                self.state_counter -= 1

            else:

                if not self.target_visible:

                    self.state = "SEARCHING"

                else:

                    # =================================
                    # TRACKING → LOCKING → LOCKED
                    # =================================

                    if not self.target_visible:

                       self.state = "SEARCHING"

                        # Reset lock progress
                       self.lock_counter = 0


                    else:

                        # Target is close enough to center

                      if (
                         abs(self.error_x) <= self.lock_threshold
                           and
                        abs(self.error_y) <= self.lock_threshold
                        ):

                          # Increase lock stability counter

                        self.lock_counter += 1


                         # Still stabilizing

                        if (
                           self.lock_counter
                              <
                           self.lock_required_frames
                            ):

                           self.state = "LOCKING"


                               # Lock completed

                        else:

                          self.state = "LOCKED"

                          self.lock_counter = (
                            self.lock_required_frames
                              )


        else:

            # Target moved away from center

              self.state = "TRACKING"

                # Reset stabilization

              self.lock_counter = 0

        # =================================
        # CLOUD MOVED AWAY
        # =================================

        if (

            self.previous_sun_occluded

            and

            not self.sun_occluded

            and

            self.current_environment == "SKY"

        ):

            if camera_can_see_target:

                self.state = "ACQUIRED"

                self.state_counter = 60

        # =================================
        # UPDATE LOCK STATUS AGAIN
        # =================================

        if self.state == "LOCKED":

            self.lock_status = "LOCKED"

        else:

            self.lock_status = "NOT LOCKED"

        # =================================
        # SAVE PREVIOUS VALUES
        # =================================

        self.previous_visible = (
            self.target_visible
        )

        self.previous_sun_occluded = (
            self.sun_occluded
        )

        # =================================
        # REDRAW
        # =================================

        self.update()


    # =================================
    # DRAW SPACE BACKGROUND
    # =================================

    def draw_space_background(self, painter):

        painter.fillRect(

            self.rect(),

            QColor(
                5,
                8,
                20
            )

        )

        painter.setPen(Qt.NoPen)

        for star in self.stars:

            brightness = (

                math.sin(

                    self.animation_time
                    *
                    star["speed"]
                    *
                    20

                    +

                    star["phase"]

                )

                +

                1

            ) / 2

            value = int(

                120
                +
                brightness * 135

            )

            painter.setBrush(

                QColor(

                    value,

                    value,

                    value

                )

            )

            size = (

                star["size"]

                *

                (

                    0.7
                    +
                    brightness * 0.6

                )

            )

            painter.drawEllipse(

                int(star["x"]),

                int(star["y"]),

                max(
                    1,
                    int(size)
                ),

                max(
                    1,
                    int(size)
                )

            )


    # =================================
    # DRAW SPACE BEACON
    # =================================

    def draw_space_beacon(self, painter):

        pulse = (

            math.sin(

                self.animation_time * 6

            )

            +

            1

        ) / 2

        glow_radius = (

            self.beacon.radius

            +

            8

            +

            pulse * 10

        )

        painter.setPen(
            Qt.NoPen
        )

        # Glow

        painter.setBrush(

            QColor(

                255,

                40,

                40,

                int(

                    50
                    +
                    pulse * 100

                )

            )

        )

        painter.drawEllipse(

            int(
                self.beacon.x
                -
                glow_radius
            ),

            int(
                self.beacon.y
                -
                glow_radius
            ),

            int(
                glow_radius * 2
            ),

            int(
                glow_radius * 2
            )

        )

        # Beacon

        painter.setBrush(

            QColor(

                255,

                int(
                    40
                    +
                    pulse * 100
                ),

                40

            )

        )

        painter.drawEllipse(

            int(
                self.beacon.x
                -
                self.beacon.radius
            ),

            int(
                self.beacon.y
                -
                self.beacon.radius
            ),

            int(
                self.beacon.radius * 2
            ),

            int(
                self.beacon.radius * 2
            )

        )


    # =================================
    # FSOC LINK QUALITY
    # =================================

    def draw_link_quality(self, painter):

        panel_x = self.width() - 300
        panel_y = 315
        panel_width = 260
        panel_height = 38

        # Simulated link quality derived from the existing tracking metrics.
        # It is not a physical RF/optical link measurement.
        if self.target_visible:
            error_magnitude = math.hypot(self.error_x, self.error_y)
            quality = max(0.0, min(100.0, self.confidence - error_magnitude * 0.12))
        else:
            quality = 0.0

        if self.state == "LOCKED" and self.target_visible:
            link_text = "OPTICAL LINK: ACTIVE"
            link_color = QColor(52, 199, 154)
        elif self.state == "OCCLUDED":
            link_text = "OPTICAL LINK: BLOCKED"
            link_color = QColor(255, 140, 0)
        elif self.target_visible:
            link_text = "OPTICAL LINK: ALIGNING"
            link_color = QColor(255, 210, 0)
        else:
            link_text = "OPTICAL LINK: OFFLINE"
            link_color = QColor(255, 80, 80)

        painter.setPen(QPen(QColor(100, 180, 255, 180), 2))
        painter.setBrush(QColor(10, 20, 35, 210))
        painter.drawRoundedRect(panel_x, panel_y, panel_width, panel_height, 10, 10)

        font = QFont()
        font.setPointSize(8)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(link_color)
        painter.drawText(panel_x + 12, panel_y + 15, link_text)

        # Quality percentage and progress bar.
        painter.setPen(QColor(220, 230, 240))
        painter.drawText(panel_x + 12, panel_y + 31, f"QUALITY {quality:.0f}%")

        bar_x = panel_x + 100
        bar_y = panel_y + 22
        bar_width = 145
        bar_height = 7

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(55, 65, 80))
        painter.drawRoundedRect(bar_x, bar_y, bar_width, bar_height, 3, 3)

        fill_width = int(bar_width * quality / 100.0)
        if fill_width > 0:
            painter.setBrush(link_color)
            painter.drawRoundedRect(bar_x, bar_y, fill_width, bar_height, 3, 3)

    # =================================
    # COMPACT OPTICAL LINK STATUS
    # =================================

    def draw_mode_optical_link(self, painter, x, y, width, mode):
        if mode == "VIDEO":
            found = self.video_target_found
            confidence = self.video_confidence
            error_x = self.video_error_x
            error_y = self.video_error_y
            locked = self.video_lock
        else:
            found = self.live_target_found
            confidence = self.live_confidence
            error_x = self.live_error_x
            error_y = self.live_error_y
            locked = self.live_lock

        error_mag = math.hypot(error_x, error_y)
        quality = max(0.0, min(100.0, confidence - error_mag * 0.10))

        if locked and found:
            label = "OPTICAL LINK: ACTIVE"
            color = QColor(52, 199, 154)
        elif found:
            label = "OPTICAL LINK: ALIGNING"
            color = QColor(230, 190, 70)
        else:
            label = "OPTICAL LINK: OFFLINE"
            color = QColor(210, 90, 90)

        h = 42
        painter.setPen(QPen(QColor(75, 105, 135), 1))
        painter.setBrush(QColor(20, 26, 34))
        painter.drawRoundedRect(x, y, width, h, 8, 8)

        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(color)
        painter.drawText(x + 12, y + 15, label)

        painter.setFont(QFont("Arial", 8, QFont.Bold))
        painter.setPen(QColor(210, 220, 230))
        painter.drawText(x + 12, y + 33, f"QUALITY {quality:.0f}%")

        bar_x = x + 86
        bar_y = y + 25
        bar_w = max(70, width - 100)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(55, 65, 78))
        painter.drawRoundedRect(bar_x, bar_y, bar_w, 7, 3, 3)
        fill_w = int(bar_w * quality / 100.0)
        if fill_w > 0:
            painter.setBrush(color)
            painter.drawRoundedRect(bar_x, bar_y, fill_w, 7, 3, 3)

    # =================================
    # RIGHT-SIDE METRIC GRAPHS
    # =================================

    def draw_graphs(self, painter):

        graph_x = self.width() - 300
        graph_width = 260

        # Compact link-quality card occupies the small space between
        # SYSTEM METRICS and the graphs.
        self.draw_link_quality(painter)

        confidence_y = 365
        confidence_height = 95

        error_y = 470
        error_height = 115

        # =================================
        # CONFIDENCE GRAPH
        # =================================

        painter.setPen(
            QPen(
                QColor(100, 180, 255, 180),
                2
            )
        )

        painter.setBrush(
            QColor(10, 20, 35, 210)
        )

        painter.drawRoundedRect(
            graph_x,
            confidence_y,
            graph_width,
            confidence_height,
            12,
            12
        )

        painter.setPen(QColor(220, 230, 240))

        graph_font = QFont()
        graph_font.setPointSize(9)
        graph_font.setBold(True)
        painter.setFont(graph_font)

        painter.drawText(
            graph_x + 12,
            confidence_y + 22,
            "CONFIDENCE (%)"
        )

        # 0% and 100% guide lines
        painter.setPen(QColor(90, 100, 115, 100))
        painter.drawLine(
            graph_x + 12,
            confidence_y + 34,
            graph_x + graph_width - 12,
            confidence_y + 34
        )
        painter.drawLine(
            graph_x + 12,
            confidence_y + confidence_height - 12,
            graph_x + graph_width - 12,
            confidence_y + confidence_height - 12
        )

        if len(self.confidence_history) >= 2:

            plot_left = graph_x + 12
            plot_right = graph_x + graph_width - 12
            plot_top = confidence_y + 34
            plot_bottom = confidence_y + confidence_height - 12

            painter.setPen(
                QPen(
                    QColor(52, 199, 154),
                    2
                )
            )

            points = []

            for i, value in enumerate(self.confidence_history):

                ratio = i / max(
                    1,
                    len(self.confidence_history) - 1
                )

                x = plot_left + ratio * (plot_right - plot_left)

                y = plot_bottom - (
                    max(0.0, min(100.0, value)) / 100.0
                ) * (plot_bottom - plot_top)

                points.append((int(x), int(y)))

            for i in range(1, len(points)):
                painter.drawLine(
                    points[i - 1][0],
                    points[i - 1][1],
                    points[i][0],
                    points[i][1]
                )

        # =================================
        # TRACKING ERROR GRAPH
        # =================================

        painter.setPen(
            QPen(
                QColor(100, 180, 255, 180),
                2
            )
        )

        painter.setBrush(
            QColor(10, 20, 35, 210)
        )

        painter.drawRoundedRect(
            graph_x,
            error_y,
            graph_width,
            error_height,
            12,
            12
        )

        painter.setPen(QColor(220, 230, 240))
        painter.setFont(graph_font)

        painter.drawText(
            graph_x + 12,
            error_y + 22,
            "TRACKING ERROR (X / Y)"
        )

        plot_left = graph_x + 12
        plot_right = graph_x + graph_width - 12
        plot_top = error_y + 34
        plot_bottom = error_y + error_height - 12
        plot_height = plot_bottom - plot_top

        max_error = 50.0

        for value in self.error_x_history:
            max_error = max(max_error, abs(value))

        for value in self.error_y_history:
            max_error = max(max_error, abs(value))

        # Zero-error reference line
        zero_y = plot_top + plot_height / 2

        painter.setPen(QColor(120, 130, 145, 130))
        painter.drawLine(
            plot_left,
            int(zero_y),
            plot_right,
            int(zero_y)
        )

        def draw_error_line(history, color):

            if len(history) < 2:
                return

            painter.setPen(
                QPen(color, 2)
            )

            points = []

            for i, value in enumerate(history):

                ratio = i / max(
                    1,
                    len(history) - 1
                )

                x = plot_left + ratio * (plot_right - plot_left)

                normalized = max(
                    -1.0,
                    min(1.0, value / max_error)
                )

                y = zero_y - normalized * (plot_height / 2)

                points.append((int(x), int(y)))

            for i in range(1, len(points)):
                painter.drawLine(
                    points[i - 1][0],
                    points[i - 1][1],
                    points[i][0],
                    points[i][1]
                )

        draw_error_line(
            self.error_x_history,
            QColor(74, 144, 226)
        )

        draw_error_line(
            self.error_y_history,
            QColor(255, 190, 0)
        )

        painter.setFont(graph_font)

        painter.setPen(QColor(74, 144, 226))
        painter.drawText(
            graph_x + 12,
            error_y + error_height - 8,
            "X"
        )

        painter.setPen(QColor(255, 190, 0))
        painter.drawText(
            graph_x + 32,
            error_y + error_height - 8,
            "Y"
        )

    # =================================
    # PAINT EVENT
    # =================================

    def paintEvent(self, event):

        painter = QPainter(self)

        # =================================
        # VIDEO / LIVE MODE
        # =================================
        if self.operating_mode != "VIRTUAL":
            painter.fillRect(self.rect(), QColor(18, 18, 18))

            if self.operating_mode == "VIDEO":
                title = "VIDEO UPLOAD TRACKING MODE"
                if self.video_frame_rgb is not None:
                    painter.drawImage(20, 55, self.video_frame_rgb)
            else:
                title = "LIVE TRACKING MODE"

            painter.setPen(QColor(74, 144, 226))
            painter.setFont(QFont("Arial", 17, QFont.Bold))
            painter.drawText(20, 86, title)

            if self.operating_mode == "VIDEO" and self.video_frame is not None:
                # ---------------------------------------------------------
                # LEFT: original video/world view with a MOVING camera box
                # RIGHT: large virtual camera view produced by that crop
                # ---------------------------------------------------------
                margin = 20
                top = 105
                panel_w = 285
                gap = 16
                source_w = 270
                source_h = min(240, max(180, self.height() - 125))
                view_x = margin + source_w + gap
                panel_x = self.width() - panel_w - margin
                view_w = max(420, panel_x - gap - view_x)
                view_h = max(360, self.height() - top - 25)

                # Original video as a world/reference view.
                source_img = self.video_frame_rgb.scaled(
                    source_w, source_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                source_x = margin
                source_y = top
                painter.drawImage(source_x, source_y, source_img)
                painter.setPen(QPen(QColor(110, 110, 110), 2))
                painter.drawRect(source_x, source_y, source_img.width(), source_img.height())
                painter.setPen(QColor(200, 200, 200))
                painter.setFont(QFont("Arial", 9, QFont.Bold))
                painter.drawText(source_x + 8, source_y + 18, "VIDEO / WORLD VIEW")

                # Camera viewport rectangle inside the original video.
                src_scale_x = source_img.width() / max(1, self.video_frame_width)
                src_scale_y = source_img.height() / max(1, self.video_frame_height)
                crop_w = max(2, int(self.video_frame_width * self.video_crop_ratio))
                crop_h = max(2, int(self.video_frame_height * self.video_crop_ratio))
                crop_x = int(round(self.video_camera_x - crop_w / 2.0))
                crop_y = int(round(self.video_camera_y - crop_h / 2.0))
                crop_x = max(0, min(crop_x, self.video_frame_width - crop_w))
                crop_y = max(0, min(crop_y, self.video_frame_height - crop_h))

                cam_rect_x = source_x + crop_x * src_scale_x
                cam_rect_y = source_y + crop_y * src_scale_y
                cam_rect_w = crop_w * src_scale_x
                cam_rect_h = crop_h * src_scale_y
                painter.setPen(QPen(QColor(52, 199, 89), 2))
                painter.drawRect(int(cam_rect_x), int(cam_rect_y), int(cam_rect_w), int(cam_rect_h))

                # Beacon position in the world view.
                if self.video_target_found:
                    wx = source_x + self.video_target_x * src_scale_x
                    wy = source_y + self.video_target_y * src_scale_y
                    painter.setPen(QPen(QColor(52, 199, 89), 2))
                    painter.drawEllipse(int(wx - 7), int(wy - 7), 14, 14)

                # Large moving camera view.
                cropped = self.video_frame_rgb.copy(crop_x, crop_y, crop_w, crop_h)
                image = cropped.scaled(
                    view_w, view_h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                painter.drawImage(view_x, top, image)
                painter.setPen(QPen(QColor(52, 199, 89), 2))
                painter.drawRect(view_x, top, image.width(), image.height())

                sx = image.width() / max(1, crop_w)
                sy = image.height() / max(1, crop_h)
                cx = view_x + image.width() / 2
                cy = top + image.height() / 2

                # Fixed camera center / crosshair.
                painter.setPen(QPen(QColor(80, 220, 255), 2))
                painter.drawLine(int(cx - 18), int(cy), int(cx + 18), int(cy))
                painter.drawLine(int(cx), int(cy - 18), int(cx), int(cy + 18))
                painter.drawEllipse(int(cx - 5), int(cy - 5), 10, 10)

                if self.video_target_found:
                    tx = view_x + (self.video_target_x - crop_x) * sx
                    ty = top + (self.video_target_y - crop_y) * sy
                    painter.setPen(QPen(QColor(52, 199, 89), 2))
                    painter.drawEllipse(int(tx - 11), int(ty - 11), 22, 22)
                    painter.drawLine(int(cx), int(cy), int(tx), int(ty))
                    painter.setFont(QFont("Arial", 10, QFont.Bold))
                    painter.drawText(int(tx + 14), int(ty - 12), "BEACON")

                # Make the camera motion obvious to the user.
                pan_x = self.video_error_x
                pan_y = self.video_error_y
                painter.setPen(QColor(74, 144, 226))
                painter.setFont(QFont("Arial", 10, QFont.Bold))
                direction = "CENTERED"
                if abs(pan_x) > 8:
                    direction = "PAN RIGHT" if pan_x > 0 else "PAN LEFT"
                elif abs(pan_y) > 8:
                    direction = "PAN DOWN" if pan_y > 0 else "PAN UP"
                painter.drawText(view_x + 12, top + 24, f"VIRTUAL CAMERA  •  {direction}")
                painter.setFont(QFont("Arial", 9))
                painter.drawText(view_x + 12, top + 44,
                                 f"Camera center: ({self.video_camera_x:.0f}, {self.video_camera_y:.0f})")

                # Metrics panel.
                metrics_h = 255
                painter.fillRect(panel_x, top, panel_w, metrics_h, QColor(28, 28, 28))
                painter.setPen(QColor(230, 230, 230))
                painter.setFont(QFont("Arial", 11, QFont.Bold))
                painter.drawText(panel_x + 15, top + 26, "VIDEO TRACKING METRICS")
                painter.setFont(QFont("Arial", 10))
                painter.drawText(panel_x + 15, top + 56, f"State: {self.state}")
                painter.drawText(panel_x + 15, top + 84, f"Beacon: {'DETECTED' if self.video_target_found else 'NOT DETECTED'}")
                painter.drawText(panel_x + 15, top + 112, f"Confidence: {self.video_confidence:.1f}%")
                painter.drawText(panel_x + 15, top + 140, f"Error X: {self.video_error_x:.1f} px")
                painter.drawText(panel_x + 15, top + 168, f"Error Y: {self.video_error_y:.1f} px")
                painter.drawText(panel_x + 15, top + 196, f"Lock: {'LOCKED' if self.video_lock else 'NOT LOCKED'}")
                painter.setPen(QColor(150, 150, 150))
                if self.video_path:
                    painter.drawText(panel_x + 15, top + 226, self.video_path.split('/')[-1][-34:])

                # Optical-link status.
                link_y = top + metrics_h + 10
                self.draw_mode_optical_link(
                    painter, panel_x, link_y, panel_w, "VIDEO"
                )

                # Video Upload performance graphs.
                graph_y = link_y + 54
                graph_h = 112

                def draw_video_graph(x, y, w, h, title_text, history, ymin, ymax, line_color):
                    painter.fillRect(x, y, w, h, QColor(18, 18, 18))
                    painter.setPen(QPen(QColor(58, 68, 82), 1))
                    painter.drawRect(x, y, w, h)
                    painter.setPen(QColor(74, 144, 226))
                    painter.setFont(QFont("Arial", 10, QFont.Bold))
                    painter.drawText(x + 12, y + 20, title_text)
                    left = x + 12
                    right = x + w - 12
                    top_p = y + 32
                    bottom = y + h - 12
                    painter.setPen(QPen(QColor(43, 49, 59), 1))
                    painter.drawLine(left, bottom, right, bottom)
                    if ymin < 0 < ymax:
                        zero_y = bottom - ((0 - ymin) / (ymax - ymin)) * (bottom - top_p)
                        painter.drawLine(left, int(zero_y), right, int(zero_y))
                    if len(history) < 2:
                        return
                    painter.setPen(QPen(line_color, 2))
                    points = []
                    for i, value in enumerate(history):
                        px = left + (i / max(1, len(history) - 1)) * (right - left)
                        norm = max(0.0, min(1.0, (float(value) - ymin) / max(1e-9, ymax - ymin)))
                        py = bottom - norm * (bottom - top_p)
                        points.append((int(px), int(py)))
                    for i in range(1, len(points)):
                        painter.drawLine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])

                draw_video_graph(panel_x, graph_y, panel_w, graph_h,
                                 "CONFIDENCE (%)", self.video_confidence_history,
                                 0, 100, QColor(52, 199, 154))

                error_graph_y = graph_y + graph_h + 14
                draw_video_graph(panel_x, error_graph_y, panel_w, graph_h,
                                 "TRACKING ERROR (X / Y)", self.video_error_x_history,
                                 -300, 300, QColor(74, 144, 226))

                if len(self.video_error_y_history) >= 2:
                    left = panel_x + 12
                    right = panel_x + panel_w - 12
                    top_p = error_graph_y + 32
                    bottom = error_graph_y + graph_h - 12
                    painter.setPen(QPen(QColor(220, 160, 55), 2))
                    points = []
                    for i, value in enumerate(self.video_error_y_history):
                        px = left + (i / max(1, len(self.video_error_y_history) - 1)) * (right - left)
                        norm = max(0.0, min(1.0, (float(value) + 300.0) / 600.0))
                        py = bottom - norm * (bottom - top_p)
                        points.append((int(px), int(py)))
                    for i in range(1, len(points)):
                        painter.drawLine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])
                    painter.setFont(QFont("Arial", 8, QFont.Bold))
                    painter.drawText(panel_x + 14, bottom + 2, "X")
                    painter.drawText(panel_x + 30, bottom + 2, "Y")

            elif self.operating_mode == "VIDEO":
                # Video mode dashboard before a file is selected.
                painter.setPen(QColor(220, 220, 220))
                painter.setFont(QFont("Arial", 12, QFont.Bold))
                painter.drawText(24, 110, "VIDEO INPUT")
                painter.setFont(QFont("Arial", 11))
                painter.drawText(24, 142, "Select a recorded video to start beacon tracking.")
                painter.drawText(24, 170, "Use Mode → Video Upload → Open Video File")
                painter.drawText(24, 198, "Frames will be processed continuously for beacon detection.")

                panel_x = self.width() - 315
                panel_y = 105
                panel_w = 285
                panel_h = 255
                painter.fillRect(panel_x, panel_y, panel_w, panel_h, QColor(28, 28, 28))
                painter.setPen(QColor(74, 144, 226))
                painter.setFont(QFont("Arial", 11, QFont.Bold))
                painter.drawText(panel_x + 15, panel_y + 26, "VIDEO TRACKING METRICS")
                painter.setPen(QColor(210, 210, 210))
                painter.setFont(QFont("Arial", 10))
                painter.drawText(panel_x + 15, panel_y + 60, "State: WAITING FOR VIDEO")
                painter.drawText(panel_x + 15, panel_y + 88, "Beacon: NOT DETECTED")
                painter.drawText(panel_x + 15, panel_y + 116, "Confidence: 0.0%")
                painter.drawText(panel_x + 15, panel_y + 144, "Error X: 0.0 px")
                painter.drawText(panel_x + 15, panel_y + 172, "Error Y: 0.0 px")
                painter.drawText(panel_x + 15, panel_y + 200, "Lock: NOT LOCKED")
                painter.setPen(QColor(120, 120, 120))
                painter.drawText(panel_x + 15, panel_y + 230, "No video selected")

                # Empty performance graphs are visible before a video is loaded.
                graph_y = panel_y + panel_h + 18
                graph_h = 118
                for gy, title_text in ((graph_y, "CONFIDENCE (%)"),
                                       (graph_y + graph_h + 14, "TRACKING ERROR (X / Y)")):
                    painter.fillRect(panel_x, gy, panel_w, graph_h, QColor(24, 29, 36))
                    painter.setPen(QPen(QColor(58, 68, 82), 1))
                    painter.drawRect(panel_x, gy, panel_w, graph_h)
                    painter.setPen(QColor(74, 144, 226))
                    painter.setFont(QFont("Arial", 10, QFont.Bold))
                    painter.drawText(panel_x + 12, gy + 20, title_text)
                    painter.setPen(QPen(QColor(43, 49, 59), 1))
                    painter.drawLine(panel_x + 12, gy + graph_h - 12, panel_x + panel_w - 12, gy + graph_h - 12)

            else:
                # ---------------------------------------------------------
                # LIVE TRACKING MODE — ORIGINAL VIEW + VIRTUAL CAMERA VIEW
                # ---------------------------------------------------------
                margin = 20
                top = 120
                panel_w = 300
                panel_x = self.width() - panel_w - margin
                gap = 20
                source_w = 360

                # Leave enough room for both views and the metrics panel.
                available_left = max(700, panel_x - margin - gap)
                source_w = min(source_w, max(280, int(available_left * 0.28)))
                view_x = margin + source_w + gap
                view_w = max(420, panel_x - gap - view_x)
                view_h = max(400, self.height() - top - 25)

                if self.live_frame_rgb is not None:
                    # =====================================================
                    # LEFT — ORIGINAL / WORLD VIEW
                    # =====================================================
                    source_img = self.live_frame_rgb.scaled(
                        source_w,
                        min(360, max(240, self.height() - 170)),
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    source_x = margin
                    source_y = top
                    painter.drawImage(source_x, source_y, source_img)

                    painter.setPen(QPen(QColor(90, 100, 115), 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(
                        source_x, source_y, source_img.width(), source_img.height()
                    )

                    painter.setPen(QColor(225, 225, 225))
                    painter.setFont(QFont("Arial", 10, QFont.Bold))
                    painter.drawText(
                        source_x + 10, source_y + 20,
                        "ORIGINAL / WORLD VIEW"
                    )

                    # Coordinate mapping from camera frame to original view.
                    sx0 = source_img.width() / max(1, self.live_frame_width)
                    sy0 = source_img.height() / max(1, self.live_frame_height)

                    crop_w = max(2, int(self.live_frame_width * self.live_crop_ratio))
                    crop_h = max(2, int(self.live_frame_height * self.live_crop_ratio))
                    crop_x = int(round(self.live_camera_x - crop_w / 2.0))
                    crop_y = int(round(self.live_camera_y - crop_h / 2.0))
                    crop_x = max(0, min(crop_x, self.live_frame_width - crop_w))
                    crop_y = max(0, min(crop_y, self.live_frame_height - crop_h))

                    # Moving green rectangle = current virtual camera FOV.
                    camera_box_x = source_x + crop_x * sx0
                    camera_box_y = source_y + crop_y * sy0
                    camera_box_w = max(3, int(crop_w * sx0))
                    camera_box_h = max(3, int(crop_h * sy0))
                    painter.setPen(QPen(QColor(52, 199, 89), 2))
                    painter.drawRect(
                        int(camera_box_x), int(camera_box_y),
                        camera_box_w, camera_box_h
                    )

                    painter.setPen(QColor(52, 199, 89))
                    painter.setFont(QFont("Arial", 9, QFont.Bold))
                    painter.drawText(
                        int(camera_box_x + 6),
                        int(camera_box_y + 16),
                        "VIRTUAL CAMERA FOV"
                    )

                    # Beacon marker in original/world view.
                    if self.live_target_found:
                        wx = source_x + self.live_target_x * sx0
                        wy = source_y + self.live_target_y * sy0
                        painter.setPen(QPen(QColor(52, 199, 89), 2))
                        painter.drawEllipse(int(wx - 8), int(wy - 8), 16, 16)
                        painter.drawLine(
                            int(wx - 13), int(wy), int(wx + 13), int(wy)
                        )
                        painter.drawLine(
                            int(wx), int(wy - 13), int(wx), int(wy + 13)
                        )

                    # =====================================================
                    # RIGHT — MOVING VIRTUAL CAMERA VIEW
                    # =====================================================
                    cropped = self.live_frame_rgb.copy(
                        crop_x, crop_y, crop_w, crop_h
                    )
                    image = cropped.scaled(
                        view_w, view_h,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation
                    )
                    painter.drawImage(view_x, top, image)

                    painter.setPen(QPen(QColor(52, 199, 89), 2))
                    painter.drawRect(
                        view_x, top, image.width(), image.height()
                    )

                    sx = image.width() / max(1, crop_w)
                    sy = image.height() / max(1, crop_h)
                    cx = view_x + image.width() / 2.0
                    cy = top + image.height() / 2.0

                    # Header inside the camera view.
                    direction = "CENTERED"
                    if abs(self.live_error_x) > 10:
                        direction = (
                            "PAN RIGHT" if self.live_error_x > 0
                            else "PAN LEFT"
                        )
                    if (
                        abs(self.live_error_y) > 10
                        and abs(self.live_error_y) > abs(self.live_error_x)
                    ):
                        direction = (
                            "PAN DOWN" if self.live_error_y > 0
                            else "PAN UP"
                        )

                    painter.setPen(QColor(74, 144, 226))
                    painter.setFont(QFont("Arial", 13, QFont.Bold))
                    painter.drawText(
                        view_x + 14, top + 25,
                        f"VIRTUAL CAMERA  •  {direction}"
                    )
                    painter.setFont(QFont("Arial", 10))
                    painter.drawText(
                        view_x + 14, top + 46,
                        f"Camera center: ({self.live_camera_x:.0f}, {self.live_camera_y:.0f})"
                    )

                    # Camera center crosshair.
                    painter.setPen(QPen(QColor(80, 220, 255), 2))
                    painter.drawLine(int(cx - 22), int(cy), int(cx + 22), int(cy))
                    painter.drawLine(int(cx), int(cy - 22), int(cx), int(cy + 22))
                    painter.drawEllipse(int(cx - 6), int(cy - 6), 12, 12)

                    # Beacon marker + error vector in camera view.
                    if self.live_target_found:
                        tx = view_x + (self.live_target_x - crop_x) * sx
                        ty = top + (self.live_target_y - crop_y) * sy
                        painter.setPen(QPen(QColor(52, 199, 89), 2))
                        painter.drawEllipse(int(tx - 13), int(ty - 13), 26, 26)
                        painter.drawLine(int(cx), int(cy), int(tx), int(ty))
                        painter.setFont(QFont("Arial", 11, QFont.Bold))
                        painter.drawText(int(tx + 18), int(ty - 12), "BEACON")

                else:
                    painter.setPen(QColor(210, 210, 210))
                    painter.setFont(QFont("Arial", 13, QFont.Bold))
                    painter.drawText(24, 145, "LIVE CAMERA INPUT")
                    painter.setFont(QFont("Arial", 11))
                    painter.drawText(24, 175, "Use Mode → Live Tracking → Start Live Camera")

                # =====================================================
                # LIVE TRACKING METRICS
                # =====================================================
                painter.fillRect(
                    panel_x, top, panel_w, 275, QColor(28, 28, 28)
                )
                painter.setPen(QColor(74, 144, 226))
                painter.setFont(QFont("Arial", 12, QFont.Bold))
                painter.drawText(
                    panel_x + 15, top + 28,
                    "LIVE TRACKING METRICS"
                )
                painter.setPen(QColor(220, 220, 220))
                painter.setFont(QFont("Arial", 10))
                painter.drawText(panel_x + 15, top + 60, f"State: {self.state}")
                painter.drawText(
                    panel_x + 15, top + 90,
                    f"Beacon: {'DETECTED' if self.live_target_found else 'NOT DETECTED'}"
                )
                painter.drawText(
                    panel_x + 15, top + 120,
                    f"Confidence: {self.live_confidence:.1f}%"
                )
                painter.drawText(
                    panel_x + 15, top + 150,
                    f"Error X: {self.live_error_x:.1f} px"
                )
                painter.drawText(
                    panel_x + 15, top + 180,
                    f"Error Y: {self.live_error_y:.1f} px"
                )
                painter.drawText(
                    panel_x + 15, top + 210,
                    f"Lock: {'LOCKED' if self.live_lock else 'NOT LOCKED'}"
                )
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(
                    panel_x + 15, top + 240,
                    "Webcam: ACTIVE" if self.live_capture is not None
                    else "Webcam: STOPPED"
                )

                # Optical-link status.
                link_y = top + 282
                self.draw_mode_optical_link(
                    painter, panel_x, link_y, panel_w, "LIVE"
                )

                # Live performance graphs.
                graph_y = link_y + 54
                graph_h = 112

                def draw_graph(x, y, w, h, title, history, ymin, ymax):
                    painter.fillRect(x, y, w, h, QColor(18, 18, 18))
                    painter.setPen(QPen(QColor(58, 68, 82), 1))
                    painter.drawRect(x, y, w, h)
                    painter.setPen(QColor(74, 144, 226))
                    painter.setFont(QFont("Arial", 10, QFont.Bold))
                    painter.drawText(x + 12, y + 20, title)
                    left, right = x + 12, x + w - 12
                    top_p, bottom = y + 32, y + h - 12
                    painter.setPen(QPen(QColor(43, 49, 59), 1))
                    painter.drawLine(left, bottom, right, bottom)
                    if ymin < 0 < ymax:
                        zy = bottom - ((0 - ymin) / (ymax - ymin)) * (bottom - top_p)
                        painter.drawLine(left, int(zy), right, int(zy))
                    if len(history) < 2:
                        return
                    painter.setPen(QPen(QColor(52, 199, 154), 2))
                    points = []
                    for i, value in enumerate(history):
                        px = left + (i / max(1, len(history) - 1)) * (right - left)
                        norm = max(0.0, min(1.0, (float(value) - ymin) / max(1e-9, ymax - ymin)))
                        py = bottom - norm * (bottom - top_p)
                        points.append((int(px), int(py)))
                    for i in range(1, len(points)):
                        painter.drawLine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])

                draw_graph(panel_x, graph_y, panel_w, graph_h, "CONFIDENCE (%)", self.live_confidence_history, 0, 100)
                draw_graph(panel_x, graph_y + graph_h + 10, panel_w, graph_h, "TRACKING ERROR (X / Y)", self.live_error_x_history, -300, 300)

                if len(self.live_error_y_history) >= 2:
                    x0, x1 = panel_x + 12, panel_x + panel_w - 12
                    y0, y1 = graph_y + graph_h + 10 + 32, graph_y + graph_h + 10 + graph_h - 12
                    painter.setPen(QPen(QColor(220, 160, 55), 2))
                    points = []
                    for i, value in enumerate(self.live_error_y_history):
                        px = x0 + (i / max(1, len(self.live_error_y_history) - 1)) * (x1 - x0)
                        norm = max(0.0, min(1.0, (float(value) + 300.0) / 600.0))
                        py = y1 - norm * (y1 - y0)
                        points.append((int(px), int(py)))
                    for i in range(1, len(points)):
                        painter.drawLine(points[i-1][0], points[i-1][1], points[i][0], points[i][1])
                    painter.setFont(QFont("Arial", 8, QFont.Bold))
                    painter.drawText(panel_x + 14, y1 + 2, "X")
                    painter.drawText(panel_x + 30, y1 + 2, "Y")

            painter.end()
            return

        # =================================
        # DRAW BACKGROUND
        # =================================

        if self.current_environment == "SPACE":

            self.draw_space_background(
                painter
            )

        elif self.current_environment == "SKY":

            self.sky_environment.draw(

                painter,

                self.width(),

                self.height()

            )

        elif self.current_environment == "OCEAN":

            self.ocean_environment.draw(

                painter,

                self.width(),

                self.height()

            )

        # =================================
        # STATUS COLORS
        # =================================

        if self.state == "SEARCHING":

            status_text = "SEARCHING TARGET"

            status_color = QColor(
                255,
                170,
                0
            )

        elif self.state == "ACQUIRED":

            status_text = "TARGET ACQUIRED"

            status_color = QColor(
                0,
                255,
                120
            )

        elif self.state == "TRACKING":

            status_text = "TRACKING TARGET"

            status_color = QColor(
                0,
                200,
                255
            )
        elif self.state == "LOCKING":

             status_text = "LOCKING TARGET..."

             status_color = QColor(
              255,
             210,
             0
            )

             camera_color = QColor(
             255,
             210,
              0
           )

        elif self.state == "LOCKED":

            status_text = "TARGET LOCKED"

            status_color = QColor(
                180,
                80,
                255
            )

        elif self.state == "OCCLUDED":

            status_text = "TARGET OCCLUDED"

            status_color = QColor(
                255,
                120,
                0
            )

        elif self.state == "LOST":

            status_text = "TARGET LOST"

            status_color = QColor(
                255,
                70,
                70
            )

        else:

            status_text = "SEARCHING TARGET"

            status_color = QColor(
                255,
                170,
                0
            )

        # During the first startup frames, show a dedicated initialization
        # state instead of briefly reporting ACQUIRED/LOCKED.
        if not self.startup_complete:
            status_text = "INITIALIZING TRACKING"
            status_color = QColor(90, 190, 255)

        camera_color = status_color

        # =================================
        # CAMERA FIELD OF VIEW
        # =================================

        camera_pen = QPen(
            camera_color
        )

        camera_pen.setWidth(3)

        painter.setPen(
            camera_pen
        )

        painter.setBrush(
            Qt.NoBrush
        )

        painter.drawRect(

            int(self.camera.x),

            int(self.camera.y),

            int(self.camera.width),

            int(self.camera.height)

        )

        # =================================
        # CAMERA CENTER
        # =================================

        center_x, center_y = (

            self.camera.get_center()

        )

        center_pen = QPen(

            QColor(
                0,
                200,
                255
            )

        )

        center_pen.setWidth(2)

        painter.setPen(
            center_pen
        )

        painter.drawLine(

            int(center_x - 20),

            int(center_y),

            int(center_x + 20),

            int(center_y)

        )

        painter.drawLine(

            int(center_x),

            int(center_y - 20),

            int(center_x),

            int(center_y + 20)

        )

        # =================================
        # DRAW TARGET
        # =================================

        if self.current_environment == "SPACE":

            self.draw_space_beacon(
                painter
            )

        elif self.current_environment == "SKY":

            # Draw sun

            self.sky_environment.draw_sun_target(

                painter,

                self.beacon.x,

                self.beacon.y,

                self.animation_time

            )

            # Draw clouds again in front
            # so they can visually cover sun

            self.sky_environment.draw_foreground_clouds(

                painter

            )

        elif self.current_environment == "OCEAN":

            self.ocean_environment.draw_target(

                painter,

                self.beacon.x,

                self.beacon.y,

                self.animation_time

            )

        # =================================
        # ALIGNMENT VECTOR
        # =================================
        # Shows the pointing error from the camera center to the target.
        # This is a visual representation of the same Error X / Error Y
        # values shown in SYSTEM METRICS.

        if self.state in (
            "ACQUIRED",
            "TRACKING",
            "LOCKING",
            "LOCKED"
        ):

            vector_pen = QPen(
                QColor(0, 220, 255, 170)
            )
            vector_pen.setWidth(2)
            painter.setPen(vector_pen)

            painter.drawLine(
                int(center_x),
                int(center_y),
                int(self.beacon.x),
                int(self.beacon.y)
            )

            # Small arrow head showing the direction of correction.
            dx = self.beacon.x - center_x
            dy = self.beacon.y - center_y
            distance = math.hypot(dx, dy)

            if distance > 8:
                ux = dx / distance
                uy = dy / distance
                px = -uy
                py = ux
                arrow_size = 8

                tip_x = self.beacon.x
                tip_y = self.beacon.y
                base_x = tip_x - ux * arrow_size
                base_y = tip_y - uy * arrow_size

                painter.drawLine(
                    int(tip_x),
                    int(tip_y),
                    int(base_x + px * 4),
                    int(base_y + py * 4)
                )
                painter.drawLine(
                    int(tip_x),
                    int(tip_y),
                    int(base_x - px * 4),
                    int(base_y - py * 4)
                )

        # =================================
        # FSOC COMMUNICATION BEAM
        # =================================
        # Shows the optical communication link only after
        # the terminal achieves a stable lock.

        if self.state == "LOCKED" and self.target_visible:

            beam_dx = self.beacon.x - center_x
            beam_dy = self.beacon.y - center_y
            beam_length = math.hypot(beam_dx, beam_dy)

            if beam_length > 1:

                # Subtle pulsing effect to indicate an active optical link.
                pulse = (math.sin(self.animation_time * 8.0) + 1.0) / 2.0
                beam_alpha = int(70 + pulse * 70)

                beam_pen = QPen(
                    QColor(0, 255, 210, beam_alpha)
                )
                beam_pen.setWidth(7)
                painter.setPen(beam_pen)

                painter.drawLine(
                    int(center_x),
                    int(center_y),
                    int(self.beacon.x),
                    int(self.beacon.y)
                )

                # Bright optical core.
                core_pen = QPen(
                    QColor(180, 255, 245, 210)
                )
                core_pen.setWidth(2)
                painter.setPen(core_pen)

                painter.drawLine(
                    int(center_x),
                    int(center_y),
                    int(self.beacon.x),
                    int(self.beacon.y)
                )

        # =================================
        # LOCK BOX
        # =================================

        if self.state == "LOCKED":

            lock_pen = QPen(

                QColor(
                    180,
                    80,
                    255
                )

            )

            lock_pen.setWidth(2)

            painter.setPen(
                lock_pen
            )

            painter.setBrush(
                Qt.NoBrush
            )

            box_size = (

                self.beacon.radius * 2
                +
                20

            )

            painter.drawRect(

                int(

                    self.beacon.x
                    -
                    box_size / 2

                ),

                int(

                    self.beacon.y
                    -
                    box_size / 2

                ),

                int(box_size),

                int(box_size)

            )

        # =================================
        # STATUS TEXT
        # =================================

        painter.setPen(
            status_color
        )

        status_font = QFont()

        status_font.setPointSize(16)

        status_font.setBold(True)

        painter.setFont(
            status_font
        )

        # Transparent status text: no opaque banner behind the state.
        painter.setPen(status_color)
        painter.setFont(status_font)
        painter.drawText(28, 52, status_text)

        # =================================
        # ENVIRONMENT NAME
        # =================================

        painter.setPen(

            QColor(
                220,
                220,
                220
            )

        )

        env_font = QFont()

        env_font.setPointSize(11)

        env_font.setBold(True)

        painter.setFont(
            env_font
        )

        painter.drawText(

            self.width() - 180,

            40,

            f"WORLD: {self.current_environment}"

        )

        # =================================
        # SYSTEM METRICS PANEL
        # =================================

        panel_x = self.width() - 300
        panel_y = 70
        panel_width = 260
        panel_height = 235

        # Panel

        panel_pen = QPen(

            QColor(
                100,
                180,
                255,
                180
            )

        )

        panel_pen.setWidth(2)

        painter.setPen(
            panel_pen
        )

        painter.setBrush(

            QColor(
                10,
                20,
                35,
                210
            )

        )

        painter.drawRoundedRect(

            panel_x,

            panel_y,

            panel_width,

            panel_height,

            12,

            12

        )

        # =================================
        # PANEL TITLE
        # =================================

        painter.setPen(

            QColor(
                100,
                200,
                255
            )

        )

        title_font = QFont()

        title_font.setPointSize(13)

        title_font.setBold(True)

        painter.setFont(
            title_font
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 35,

            "SYSTEM METRICS"

        )

        # =================================
        # METRIC FONT
        # =================================

        metric_font = QFont()

        metric_font.setPointSize(11)

        painter.setFont(
            metric_font
        )

        label_color = QColor(
            220,
            220,
            220
        )

        # =================================
        # STATE
        # =================================

        painter.setPen(
            label_color
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 75,

            "State:"

        )

        painter.setPen(
            status_color
        )

        painter.drawText(

            panel_x + 110,

            panel_y + 75,

            self.state

        )

        # =================================
        # VISIBILITY
        # =================================

        painter.setPen(
            label_color
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 105,

            "Visibility:"

        )

        if self.target_visible:

            visibility_text = "VISIBLE"

            visibility_color = QColor(
                0,
                255,
                120
            )

        else:

            visibility_text = "NOT VISIBLE"

            visibility_color = QColor(
                255,
                80,
                80
            )

        painter.setPen(
            visibility_color
        )

        painter.drawText(

            panel_x + 110,

            panel_y + 105,

            visibility_text

        )

        # =================================
        # CONFIDENCE
        # =================================

        painter.setPen(
            label_color
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 135,

            "Confidence:"

        )

        painter.setPen(

            QColor(
                255,
                220,
                80
            )

        )

        painter.drawText(

            panel_x + 130,

            panel_y + 135,

            f"{self.confidence:.1f}%"

        )

        # =================================
        # ERROR X
        # =================================

        painter.setPen(
            label_color
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 165,

            "Error X:"

        )

        painter.setPen(

            QColor(
                0,
                200,
                255
            )

        )

        painter.drawText(

            panel_x + 110,

            panel_y + 165,

            f"{self.error_x:.1f} px"

        )

        # =================================
        # ERROR Y
        # =================================

        painter.setPen(
            label_color
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 195,

            "Error Y:"

        )

        painter.setPen(

            QColor(
                0,
                200,
                255
            )

        )

        painter.drawText(

            panel_x + 110,

            panel_y + 195,

            f"{self.error_y:.1f} px"

        )

        # =================================
        # LOCK STATUS
        # =================================

        painter.setPen(
            label_color
        )

        painter.drawText(

            panel_x + 20,

            panel_y + 225,

            "Lock:"

        )

        if self.lock_status == "LOCKED":

            lock_color = QColor(
                180,
                80,
                255
            )

        else:

            lock_color = QColor(
                255,
                100,
                100
            )

        painter.setPen(
            lock_color
        )

        painter.drawText(

            panel_x + 110,

            panel_y + 225,

            self.lock_status

        )

        # =================================
        # DISTURBANCE STATUS
        # =================================
        # Keep the dashboard clean: disturbance information is shown
        # only when the user has explicitly enabled a disturbance mode.
        if self.disturbances_enabled:
            painter.setPen(label_color)
            painter.drawText(
                panel_x + 20,
                panel_y + 255,
                "Disturbance:"
            )

            painter.setPen(QColor(255, 170, 0))
            mode_label = {
                "CAMERA": "CAMERA",
                "BEACON": "BEACON",
                "BOTH": "BOTH",
                "OFF": "OFF"
            }.get(self.disturbance_mode, "OFF")
            painter.drawText(
                panel_x + 110,
                panel_y + 255,
                mode_label + " / " + self.disturbance_strength_name
            )

        # =================================
        # RIGHT-SIDE PERFORMANCE GRAPHS
        # =================================
        # Always show the core graphs. They are independent of whether
        # disturbance mode is enabled.
        self.draw_graphs(painter)

        # =================================
        # DISTURBANCE PERFORMANCE PANEL
        # =================================

        if not self.disturbances_enabled:
            painter.end()
            return

        performance_x = self.width() - 300
        performance_y = 665
        performance_width = 260
        performance_height = 82

        painter.setPen(
            QPen(QColor(70, 150, 220), 1)
        )
        painter.setBrush(
            QColor(8, 16, 30, 235)
        )

        painter.drawRoundedRect(
            performance_x,
            performance_y,
            performance_width,
            performance_height,
            10,
            10
        )

        performance_font = QFont()
        performance_font.setPointSize(10)
        performance_font.setBold(True)
        painter.setFont(performance_font)
        painter.setPen(QColor(90, 190, 255))
        painter.drawText(
            performance_x + 12,
            performance_y + 20,
            "DISTURBANCE RESPONSE"
        )

        normal_font = QFont()
        normal_font.setPointSize(9)
        normal_font.setBold(False)
        painter.setFont(normal_font)
        painter.setPen(QColor(220, 220, 220))
        painter.drawText(
            performance_x + 12,
            performance_y + 45,
            f"Peak Error: {self.disturbance_peak_error:.1f} px"
        )
        painter.drawText(
            performance_x + 12,
            performance_y + 66,
            f"Events: {self.disturbance_event_count}"
        )

        # =================================
        # OCCLUSION MESSAGE
        # =================================

        if self.state == "OCCLUDED":

            painter.setPen(

                QColor(
                    255,
                    120,
                    0
                )

            )

            info_font = QFont()

            info_font.setPointSize(11)

            info_font.setBold(True)

            painter.setFont(
                info_font
            )

            painter.drawText(
                28,
                92,
                "SIGNAL BLOCKED BY CLOUD"
            )

        # =================================
        # LOCK MESSAGE
        # =================================

        elif self.state == "LOCKED":

            painter.setPen(

                QColor(
                    180,
                    80,
                    255
                )

            )

            lock_font = QFont()

            lock_font.setPointSize(11)

            lock_font.setBold(True)

            painter.setFont(
                lock_font
            )

            painter.drawText(
                28,
                92,
                "LOCK CONDITION: STABLE"
            )

        # =================================
        # HEADER MENU CONTROLS
        # =================================
        # Environment, pause/resume, reset and help controls are
        # available from the header menu. Keyboard shortcuts remain active.

        # =================================
        # ACTIVE OPERATING MODE
        # =================================

        painter.setPen(QColor(190, 190, 190))
        painter.setFont(QFont("Arial", 9))
        painter.drawText(
            28,
            72,
            "MODE: VIRTUAL SIMULATION  •  TRACKING ACTIVE"
        )

        # =================================
        # RIGHT-SIDE GRAPHS
        # =================================

        self.draw_graphs(painter)

        painter.end()


    def closeEvent(self, event):
        if self.video_capture is not None:
            self.video_capture.release()
            self.video_capture = None
        if self.live_capture is not None:
            self.live_capture.release()
            self.live_capture = None
        event.accept()


    # =================================
    # KEYBOARD CONTROLS
    # =================================

    def keyPressEvent(self, event):

        # =================================
        # SPACE WORLD
        # =================================

        if event.key() == Qt.Key_1:

            self.current_environment = "SPACE"

            self.sun_occluded = False

            self.update()

        # =================================
        # SKY WORLD
        # =================================

        elif event.key() == Qt.Key_2:

            self.current_environment = "SKY"

            self.update()

        # =================================
        # OCEAN WORLD
        # =================================

        elif event.key() == Qt.Key_3:

            self.current_environment = "OCEAN"

            self.sun_occluded = False

            self.update()

        # =================================
        # PAUSE
        # =================================

        elif event.key() == Qt.Key_Space:

            self.is_running = (
                not self.is_running
            )

        # =================================
        # DISTURBANCES
        # =================================

        elif event.key() == Qt.Key_D:

            self.toggle_disturbances()

        # =================================
        # DISTURBANCE MODES
        # =================================

        elif event.key() == Qt.Key_C:

            self.set_disturbance_mode("CAMERA")

        elif event.key() == Qt.Key_B:

            self.set_disturbance_mode("BEACON")

        elif event.key() == Qt.Key_X:

            self.set_disturbance_mode("BOTH")

        elif event.key() == Qt.Key_N:

            self.set_disturbance_mode("OFF")

        # =================================
        # DISTURBANCE STRENGTH
        # =================================

        elif event.key() == Qt.Key_L:

            self.set_disturbance_strength("LOW")

        elif event.key() == Qt.Key_M:

            self.set_disturbance_strength("MEDIUM")

        elif event.key() == Qt.Key_H:

            self.set_disturbance_strength("HIGH")

        # =================================
        # RESET
        # =================================

        elif event.key() == Qt.Key_R:

            # Reset beacon

            self.beacon.x = 300
            self.beacon.y = 200

            self.beacon.vx = 2.5
            self.beacon.vy = 1.8

            # Reset sun

            self.sky_sun_progress = 0.08

            self.sun_occluded = False

            self.previous_sun_occluded = False

            # Reset camera

            self.camera.x = 250
            self.camera.y = 150

            # Support both camera versions

            if hasattr(
                self.camera,
                "search_direction"
            ):

                self.camera.search_direction = 1

            if hasattr(
                self.camera,
                "search_vertical_direction"
            ):

                self.camera.search_vertical_direction = 1

            # Reset state

            self.state = "SEARCHING"

            self.target_visible = False

            self.previous_visible = False

            self.error_x = 0.0
            self.error_y = 0.0

            self.confidence = 0.0

            self.lock_status = "NOT LOCKED"

            self.state_counter = 0
            self.lock_counter = 0

            self.disturbance_mode = "OFF"
            self.disturbances_enabled = False
            self.disturbance_beacon_x = self.beacon.x
            self.disturbance_beacon_y = self.beacon.y

            # Reset graph history
            self.confidence_history.clear()
            self.error_x_history.clear()
            self.error_y_history.clear()

            self.is_running = True

            self.update()

        else:

            super().keyPressEvent(event)
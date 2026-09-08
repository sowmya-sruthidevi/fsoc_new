import random
import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from src.simulation.beacon import Beacon
from src.simulation.camera import VirtualCamera
from src.tracking.controller import TrackingController


class Environment(QWidget):

    def __init__(self):

        super().__init__()

        # ---------------------------------
        # WINDOW SIZE
        # ---------------------------------

        self.setMinimumSize(1000, 650)

        # ---------------------------------
        # SPACE ENVIRONMENT
        # ---------------------------------

        self.stars = []

        for _ in range(180):

            star = {
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
            }

            self.stars.append(star)

        # Animation time
        self.animation_time = 0.0

        # ---------------------------------
        # CREATE BEACON
        # ---------------------------------

        self.beacon = Beacon(
            x=300,
            y=200
        )

        # ---------------------------------
        # CREATE VIRTUAL CAMERA
        # ---------------------------------

        self.camera = VirtualCamera(
            x=250,
            y=150,
            width=350,
            height=250
        )

        # ---------------------------------
        # CREATE TRACKING CONTROLLER
        # ---------------------------------

        self.controller = TrackingController()

        # ---------------------------------
        # TARGET VISIBILITY
        # ---------------------------------

        self.target_visible = False
        self.previous_visible = False

        # ---------------------------------
        # SIMULATION STATE
        # ---------------------------------

        self.state = "SEARCHING"

        # Temporary state counter
        self.state_counter = 0

        # ---------------------------------
        # TRACKING ERROR
        # ---------------------------------

        self.error_x = 0.0
        self.error_y = 0.0

        # ---------------------------------
        # LOCK THRESHOLD
        # ---------------------------------

        self.lock_threshold = 80.0

        # ---------------------------------
        # SIMULATION RUNNING STATE
        # ---------------------------------

        self.is_running = True

        # ---------------------------------
        # TIMER
        # ---------------------------------

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_simulation
        )

        # Approximately 60 FPS
        self.timer.start(16)


    def update_simulation(self):

        # ---------------------------------
        # UPDATE ANIMATION
        # ---------------------------------

        self.animation_time += 0.05

        # ---------------------------------
        # PAUSE SIMULATION
        # ---------------------------------

        if not self.is_running:

            self.update()
            return

        # ---------------------------------
        # MOVE BEACON
        # ---------------------------------

        self.beacon.update(
            self.width(),
            self.height()
        )

        # ---------------------------------
        # CHECK TARGET VISIBILITY
        # ---------------------------------

        self.target_visible = (
            self.camera.is_target_visible(
                self.beacon.x,
                self.beacon.y
            )
        )

        # ---------------------------------
        # TARGET ENTERED CAMERA FOV
        # ---------------------------------

        if (
            self.target_visible
            and not self.previous_visible
        ):

            self.state = "ACQUIRED"

            # Show acquired temporarily
            self.state_counter = 60

        # ---------------------------------
        # TARGET LEFT CAMERA FOV
        # ---------------------------------

        elif (
            not self.target_visible
            and self.previous_visible
        ):

            self.state = "LOST"

            # Show lost temporarily
            self.state_counter = 60

        # ---------------------------------
        # CAMERA BEHAVIOR
        # ---------------------------------

        if self.target_visible:

            # Calculate tracking error

            self.error_x, self.error_y = (
                self.camera.calculate_error(
                    self.beacon.x,
                    self.beacon.y
                )
            )

            # Controller calculates movement

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

        else:

            # Search for beacon

            self.camera.search(
                self.width(),
                self.height()
            )

        # ---------------------------------
        # RECALCULATE ERROR
        # ---------------------------------

        self.error_x, self.error_y = (
            self.camera.calculate_error(
                self.beacon.x,
                self.beacon.y
            )
        )

        # ---------------------------------
        # HANDLE TEMPORARY STATES
        # ---------------------------------

        if self.state_counter > 0:

            self.state_counter -= 1

        else:

            if not self.target_visible:

                self.state = "SEARCHING"

            else:

                # Check lock condition

                if (
                    abs(self.error_x)
                    <= self.lock_threshold

                    and

                    abs(self.error_y)
                    <= self.lock_threshold
                ):

                    self.state = "LOCKED"

                else:

                    self.state = "TRACKING"

        # ---------------------------------
        # SAVE PREVIOUS VISIBILITY
        # ---------------------------------

        self.previous_visible = (
            self.target_visible
        )

        # ---------------------------------
        # REDRAW SCREEN
        # ---------------------------------

        self.update()


    def paintEvent(self, event):

        painter = QPainter(self)

        # ---------------------------------
        # DRAW SPACE BACKGROUND
        # ---------------------------------

        painter.fillRect(
            self.rect(),
            QColor(5, 8, 20)
        )

        # ---------------------------------
        # DRAW WHITE BLINKING STARS
        # ---------------------------------

        painter.setPen(Qt.NoPen)

        for star in self.stars:

            # Calculate blinking brightness

            brightness = (
                math.sin(
                    self.animation_time
                    * star["speed"]
                    * 20

                    + star["phase"]
                )

                + 1
            ) / 2

            # White / light gray stars

            value = int(
                120
                + brightness * 135
            )

            painter.setBrush(
                QColor(
                    value,
                    value,
                    value
                )
            )

            # Slight size variation

            size = (
                star["size"]
                * (
                    0.7
                    + brightness * 0.6
                )
            )

            painter.drawEllipse(

                int(star["x"]),

                int(star["y"]),

                max(1, int(size)),

                max(1, int(size))

            )

        # ---------------------------------
        # STATUS COLORS
        # ---------------------------------

        if self.state == "SEARCHING":

            status_text = "SEARCHING TARGET"

            status_color = QColor(
                255,
                170,
                0
            )

            camera_color = QColor(
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

            camera_color = QColor(
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

            camera_color = QColor(
                0,
                200,
                255
            )

        elif self.state == "LOCKED":

            status_text = "TARGET LOCKED"

            status_color = QColor(
                180,
                80,
                255
            )

            camera_color = QColor(
                180,
                80,
                255
            )

        elif self.state == "LOST":

            status_text = "TARGET LOST"

            status_color = QColor(
                255,
                70,
                70
            )

            camera_color = QColor(
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

            camera_color = QColor(
                255,
                170,
                0
            )

        # ---------------------------------
        # DRAW CAMERA FOV
        # ---------------------------------

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

        # ---------------------------------
        # DRAW CAMERA CENTER CROSSHAIR
        # ---------------------------------

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

        # Horizontal crosshair

        painter.drawLine(

            int(center_x - 20),

            int(center_y),

            int(center_x + 20),

            int(center_y)

        )

        # Vertical crosshair

        painter.drawLine(

            int(center_x),

            int(center_y - 20),

            int(center_x),

            int(center_y + 20)

        )

        # ---------------------------------
        # DRAW BLINKING BEACON GLOW
        # ---------------------------------

        beacon_pulse = (

            math.sin(
                self.animation_time * 6
            )

            + 1

        ) / 2

        # Glow radius changes

        glow_radius = (

            self.beacon.radius

            + 8

            + beacon_pulse * 10

        )

        # Outer red glow

        painter.setBrush(

            QColor(
                255,
                40,
                40,
                int(
                    50
                    + beacon_pulse * 100
                )
            )

        )

        painter.setPen(
            Qt.NoPen
        )

        painter.drawEllipse(

            int(
                self.beacon.x
                - glow_radius
            ),

            int(
                self.beacon.y
                - glow_radius
            ),

            int(
                glow_radius * 2
            ),

            int(
                glow_radius * 2
            )

        )

        # ---------------------------------
        # DRAW MAIN BEACON
        # ---------------------------------

        beacon_red = 255

        beacon_green = int(
            40
            + beacon_pulse * 100
        )

        painter.setBrush(

            QColor(
                beacon_red,
                beacon_green,
                40
            )

        )

        painter.drawEllipse(

            int(
                self.beacon.x
                - self.beacon.radius
            ),

            int(
                self.beacon.y
                - self.beacon.radius
            ),

            int(
                self.beacon.radius * 2
            ),

            int(
                self.beacon.radius * 2
            )

        )

        # ---------------------------------
        # DRAW LOCK BOX
        # ---------------------------------

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

                + 14

            )

            painter.drawRect(

                int(
                    self.beacon.x
                    - box_size / 2
                ),

                int(
                    self.beacon.y
                    - box_size / 2
                ),

                int(box_size),

                int(box_size)

            )

        # ---------------------------------
        # DRAW STATUS TEXT
        # ---------------------------------

        painter.setPen(
            status_color
        )

        status_font = QFont()

        status_font.setPointSize(16)

        status_font.setBold(True)

        painter.setFont(
            status_font
        )

        painter.drawText(

            30,

            50,

            status_text

        )

        # ---------------------------------
        # DRAW ERROR TEXT
        # ---------------------------------

        painter.setPen(

            QColor(
                220,
                220,
                220
            )

        )

        error_font = QFont()

        error_font.setPointSize(12)

        painter.setFont(
            error_font
        )

        error_text = (

            f"Error X: {self.error_x:.1f} px"

            f"    "

            f"Error Y: {self.error_y:.1f} px"

        )

        painter.drawText(

            30,

            85,

            error_text

        )

        # ---------------------------------
        # DRAW LOCK INFORMATION
        # ---------------------------------

        if self.state == "LOCKED":

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

                30,

                115,

                "LOCK CONDITION: STABLE"

            )

        # ---------------------------------
        # DRAW CONTROL INSTRUCTIONS
        # ---------------------------------

        painter.setPen(
            QColor(
                150,
                150,
                150
            )
        )

        control_font = QFont()

        control_font.setPointSize(10)

        painter.setFont(
            control_font
        )

        painter.drawText(

            30,

            self.height() - 50,

            "SPACE → Pause / Resume"

        )

        painter.drawText(

            30,

            self.height() - 25,

            "R → Reset Simulation"

        )

        painter.end()


    def keyPressEvent(self, event):

        # ---------------------------------
        # SPACE = PAUSE / RESUME
        # ---------------------------------

        if event.key() == Qt.Key_Space:

            self.is_running = (
                not self.is_running
            )

            if self.is_running:

                print(
                    "Simulation Started"
                )

            else:

                print(
                    "Simulation Paused"
                )

        # ---------------------------------
        # R = RESET SIMULATION
        # ---------------------------------

        elif event.key() == Qt.Key_R:

            # Reset beacon position

            self.beacon.x = 300
            self.beacon.y = 200

            # Reset beacon velocity

            self.beacon.vx = 2.5
            self.beacon.vy = 1.8

            # Reset camera position

            self.camera.x = 250
            self.camera.y = 150

            # Reset camera search directions

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

            # Reset errors

            self.error_x = 0.0
            self.error_y = 0.0

            self.state_counter = 0

            # Start simulation

            self.is_running = True

            self.update()

            print(
                "Simulation Reset"
            )

        else:

            super().keyPressEvent(event)
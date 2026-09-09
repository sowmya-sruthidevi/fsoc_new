import random
import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter, QColor, QPen, QFont

from src.simulation.beacon import Beacon
from src.simulation.camera import VirtualCamera
from src.simulation.sky_environment import SkyEnvironment
from src.simulation.ocean_environment import OceanEnvironment
from src.tracking.controller import TrackingController


class Environment(QWidget):

    def __init__(self):

        super().__init__()

        self.setMinimumSize(1000, 650)
        self.setFocusPolicy(Qt.StrongFocus)

        # =================================
        # CURRENT ENVIRONMENT
        # =================================

        self.current_environment = "SPACE"

        # =================================
        # CREATE ENVIRONMENTS
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
        # ANIMATION TIME
        # =================================

        self.animation_time = 0.0

        # =================================
        # SKY SUN MOVEMENT
        # =================================

        # 0 = left side
        # 1 = right side
        self.sky_sun_progress = 0.08

        # Speed of sun movement
        # Smaller value = slower movement
        self.sky_sun_speed = 0.00025

        # =================================
        # CREATE TARGET
        # =================================

        self.beacon = Beacon(
            x=300,
            y=200
        )

        # =================================
        # CREATE CAMERA
        # =================================

        self.camera = VirtualCamera(
            x=250,
            y=150,
            width=350,
            height=250
        )

        # =================================
        # TRACKING CONTROLLER
        # =================================

        self.controller = TrackingController()

        # =================================
        # TARGET VISIBILITY
        # =================================

        self.target_visible = False
        self.previous_visible = False

        # =================================
        # SIMULATION STATE
        # =================================

        self.state = "SEARCHING"
        self.state_counter = 0

        # =================================
        # TRACKING ERROR
        # =================================

        self.error_x = 0.0
        self.error_y = 0.0

        # =================================
        # LOCK THRESHOLD
        # =================================

        self.lock_threshold = 80.0

        # =================================
        # SIMULATION RUNNING
        # =================================

        self.is_running = True

        # =================================
        # TIMER
        # =================================

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self.update_simulation
        )

        # Approximately 60 FPS
        self.timer.start(16)


    # =================================
    # UPDATE SIMULATION
    # =================================

    def update_simulation(self):

        # =================================
        # UPDATE ANIMATION TIME
        # =================================

        self.animation_time += 0.05

        # =================================
        # UPDATE ENVIRONMENT ANIMATIONS
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
        # PAUSE SIMULATION
        # =================================

        if not self.is_running:

            self.update()
            return

        # =================================
        # MOVE TARGET
        # =================================

        if self.current_environment == "SPACE":

            # Normal beacon movement

            self.beacon.update(
                self.width(),
                self.height()
            )


        elif self.current_environment == "SKY":

            # =================================
            # REALISTIC SLOW SUN MOVEMENT
            # =================================

            # Slowly increase sun progress
            self.sky_sun_progress += (
                self.sky_sun_speed
            )

            # =================================
            # SUN REACHES END OF SKY
            # =================================

            if self.sky_sun_progress >= 1.0:

                # Restart from left side
                self.sky_sun_progress = 0.0

                # Target was lost
                self.state = "SEARCHING"

                self.target_visible = False
                self.previous_visible = False

            # =================================
            # SUN HORIZONTAL MOVEMENT
            # =================================

            # Sun moves from left to right

            start_x = (
                -self.beacon.radius
            )

            end_x = (
                self.width()
                + self.beacon.radius
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
            # SUN CURVED PATH
            # =================================

            # Sun starts lower
            # Moves upward
            # Reaches highest point
            # Slowly moves downward

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

            # Subtract because screen Y
            # increases downward

            self.beacon.y = (

                horizon_y
                -
                sun_arc

            )

            # =================================
            # KEEP SUN INSIDE SAFE AREA
            # =================================

            self.beacon.y = max(

                self.beacon.radius + 40,

                min(

                    self.beacon.y,

                    self.height()
                    -
                    self.beacon.radius
                    -
                    80

                )

            )


        elif self.current_environment == "OCEAN":

            # Normal UAV / target movement

            self.beacon.update(
                self.width(),
                self.height()
            )

        # =================================
        # CHECK TARGET VISIBILITY
        # =================================

        self.target_visible = (

            self.camera.is_target_visible(

                self.beacon.x,
                self.beacon.y

            )

        )

        # =================================
        # STATE TRANSITIONS
        # =================================

        if (

            self.target_visible

            and

            not self.previous_visible

        ):

            self.state = "ACQUIRED"

            self.state_counter = 60


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

        if self.target_visible:

            # =================================
            # CALCULATE TRACKING ERROR
            # =================================

            self.error_x, self.error_y = (

                self.camera.calculate_error(

                    self.beacon.x,
                    self.beacon.y

                )

            )

            # =================================
            # CONTROLLER MOVEMENT
            # =================================

            move_x, move_y = (

                self.controller.calculate_movement(

                    self.error_x,
                    self.error_y

                )

            )

            # =================================
            # MOVE CAMERA
            # =================================

            self.camera.move(

                move_x,
                move_y,

                self.width(),
                self.height()

            )

        else:

            # =================================
            # SEARCH FOR TARGET
            # =================================

            self.camera.search(

                self.width(),
                self.height()

            )

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
        # UPDATE STATE
        # =================================

        if self.state_counter > 0:

            self.state_counter -= 1

        else:

            if not self.target_visible:

                self.state = "SEARCHING"

            else:

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

        # =================================
        # SAVE PREVIOUS VISIBILITY
        # =================================

        self.previous_visible = (

            self.target_visible

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

        painter.setPen(
            Qt.NoPen
        )

        # =================================
        # DRAW STARS
        # =================================

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

                + 1

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

            + 1

        ) / 2

        # =================================
        # BEACON GLOW
        # =================================

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

        # =================================
        # MAIN BEACON
        # =================================

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
    # PAINT EVENT
    # =================================

    def paintEvent(self, event):

        painter = QPainter(self)

        # =================================
        # DRAW ENVIRONMENT
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

            camera_color = status_color


        elif self.state == "ACQUIRED":

            status_text = "TARGET ACQUIRED"

            status_color = QColor(
                0,
                255,
                120
            )

            camera_color = status_color


        elif self.state == "TRACKING":

            status_text = "TRACKING TARGET"

            status_color = QColor(
                0,
                200,
                255
            )

            camera_color = status_color


        elif self.state == "LOCKED":

            status_text = "TARGET LOCKED"

            status_color = QColor(
                180,
                80,
                255
            )

            camera_color = status_color


        elif self.state == "LOST":

            status_text = "TARGET LOST"

            status_color = QColor(
                255,
                70,
                70
            )

            camera_color = status_color


        else:

            status_text = "SEARCHING TARGET"

            status_color = QColor(
                255,
                170,
                0
            )

            camera_color = status_color

        # =================================
        # DRAW CAMERA FIELD OF VIEW
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
        # DRAW CAMERA CENTER
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

        # Horizontal center line

        painter.drawLine(

            int(center_x - 20),

            int(center_y),

            int(center_x + 20),

            int(center_y)

        )

        # Vertical center line

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

            self.sky_environment.draw_sun_target(

                painter,

                self.beacon.x,

                self.beacon.y,

                self.animation_time

            )


        elif self.current_environment == "OCEAN":

            self.ocean_environment.draw_target(

                painter,

                self.beacon.x,

                self.beacon.y,

                self.animation_time

            )

        # =================================
        # DRAW LOCK BOX
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
        # DRAW STATUS TEXT
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

        painter.drawText(

            30,
            50,

            status_text

        )

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
        # ERROR TEXT
        # =================================

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

        # =================================
        # LOCK INFORMATION
        # =================================

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

        # =================================
        # CONTROLS
        # =================================

        painter.setPen(

            QColor(
                180,
                180,
                180
            )

        )

        control_font = QFont()

        control_font.setPointSize(10)

        painter.setFont(
            control_font
        )

        painter.drawText(

            30,

            self.height() - 95,

            "1 → SPACE ENVIRONMENT"

        )

        painter.drawText(

            30,

            self.height() - 70,

            "2 → SKY ENVIRONMENT"

        )

        painter.drawText(

            30,

            self.height() - 45,

            "3 → OCEAN ENVIRONMENT"

        )

        painter.drawText(

            30,

            self.height() - 20,

            "SPACE → Pause/Resume     R → Reset"

        )

        painter.end()


    # =================================
    # KEYBOARD CONTROLS
    # =================================

    def keyPressEvent(self, event):

        # =================================
        # 1 = SPACE ENVIRONMENT
        # =================================

        if event.key() == Qt.Key_1:

            self.current_environment = "SPACE"

            self.update()


        # =================================
        # 2 = SKY ENVIRONMENT
        # =================================

        elif event.key() == Qt.Key_2:

            self.current_environment = "SKY"

            self.update()


        # =================================
        # 3 = OCEAN ENVIRONMENT
        # =================================

        elif event.key() == Qt.Key_3:

            self.current_environment = "OCEAN"

            self.update()


        # =================================
        # SPACE = PAUSE / RESUME
        # =================================

        elif event.key() == Qt.Key_Space:

            self.is_running = (

                not self.is_running

            )


        # =================================
        # R = RESET
        # =================================

        elif event.key() == Qt.Key_R:

            # =================================
            # RESET BEACON
            # =================================

            self.beacon.x = 300
            self.beacon.y = 200

            self.beacon.vx = 2.5
            self.beacon.vy = 1.8

            # =================================
            # RESET SKY SUN
            # =================================

            self.sky_sun_progress = 0.08

            # =================================
            # RESET CAMERA
            # =================================

            self.camera.x = 250
            self.camera.y = 150

            self.camera.search_direction = 1

            # Reset vertical direction

            if hasattr(

                self.camera,

                "search_vertical_direction"

            ):

                self.camera.search_vertical_direction = 1

            # =================================
            # RESET SIMULATION STATE
            # =================================

            self.state = "SEARCHING"

            self.target_visible = False

            self.previous_visible = False

            self.error_x = 0.0
            self.error_y = 0.0

            self.state_counter = 0

            self.is_running = True

            self.update()


        else:

            super().keyPressEvent(event)
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

        self.sky_sun_progress = 0.08

        self.sky_sun_speed = 0.00025

        # =================================
        # SUN OCCLUSION
        # =================================

        self.sun_occluded = False

        self.previous_sun_occluded = False

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

            self.beacon.update(
                self.width(),
                self.height()
            )


        elif self.current_environment == "SKY":

            # =================================
            # SLOW SUN MOVEMENT
            # =================================

            self.sky_sun_progress += (
                self.sky_sun_speed
            )

            # =================================
            # SUN REACHES END
            # =================================

            if self.sky_sun_progress >= 1.0:

                self.sky_sun_progress = 0.0

                self.state = "SEARCHING"

                self.target_visible = False
                self.previous_visible = False

                self.sun_occluded = False
                self.previous_sun_occluded = False

            # =================================
            # SUN HORIZONTAL MOVEMENT
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
            # SUN CURVED PATH
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
            # KEEP SUN INSIDE SCREEN
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

            self.beacon.update(
                self.width(),
                self.height()
            )

            self.sun_occluded = False


        else:

            self.sun_occluded = False

        # =================================
        # CHECK CAMERA VISIBILITY
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

        # In SKY environment:
        # Even if the camera points correctly,
        # the target is not visible when a
        # cloud blocks the sun.

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
        # CLOUD OCCLUSION STATE
        # =================================

        if (

            self.current_environment == "SKY"

            and

            self.sun_occluded

        ):

            # Cloud naturally blocks the sun

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

        if self.target_visible:

            # Calculate error

            self.error_x, self.error_y = (

                self.camera.calculate_error(

                    self.beacon.x,
                    self.beacon.y

                )

            )

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

        else:

            # =================================
            # SEARCH ONLY WHEN NOT OCCLUDED
            # =================================

            # When the cloud blocks the sun,
            # the camera should not immediately
            # behave as if the target vanished
            # permanently.

            if self.state != "OCCLUDED":

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
        # UPDATE NORMAL STATE
        # =================================

        if self.state != "OCCLUDED":

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
        # CLOUD JUST MOVED AWAY
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
        # SAVE PREVIOUS STATUS
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

        # Main beacon

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
        # DRAW ENVIRONMENT BACKGROUND
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


        elif self.state == "OCCLUDED":

            status_text = "TARGET OCCLUDED"

            status_color = QColor(
                255,
                120,
                0
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

            # Draw sun first

            self.sky_environment.draw_sun_target(

                painter,

                self.beacon.x,

                self.beacon.y,

                self.animation_time

            )

            # ---------------------------------
            # DRAW CLOUDS IN FRONT OF SUN
            # ---------------------------------

            # This is what visually makes the
            # cloud cover the sun.

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
        # OCCLUSION INFORMATION
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

                30,

                115,

                "SIGNAL BLOCKED BY CLOUD"

            )

        # =================================
        # LOCK INFORMATION
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

            self.sun_occluded = False

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

            self.sun_occluded = False

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

            self.camera.search_direction = 1

            if hasattr(

                self.camera,

                "search_vertical_direction"

            ):

                self.camera.search_vertical_direction = 1

            # Reset simulation state

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
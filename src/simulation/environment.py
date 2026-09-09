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
            x=250,
            y=150,
            width=350,
            height=250
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
        # RUNNING
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

        # Animation

        self.animation_time += 0.05

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

            # Search only when target
            # is not temporarily occluded

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
    # PAINT EVENT
    # =================================

    def paintEvent(self, event):

        painter = QPainter(self)

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

                30,

                115,

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

            self.is_running = True

            self.update()

        else:

            super().keyPressEvent(event)
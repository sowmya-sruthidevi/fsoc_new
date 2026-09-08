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

        # Target is considered locked when
        # both errors are below this value.

        self.lock_threshold = 80.0
         # Simulation running state
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
           # Pause simulation
        if not self.is_running:
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

            # Show ACQUIRED temporarily
            self.state_counter = 60


        # ---------------------------------
        # TARGET LEFT CAMERA FOV
        # ---------------------------------

        elif (
            not self.target_visible
            and self.previous_visible
        ):

            self.state = "LOST"

            # Show LOST temporarily
            self.state_counter = 60


        # ---------------------------------
        # CAMERA BEHAVIOR
        # ---------------------------------

        if self.target_visible:

            # ---------------------------------
            # CALCULATE ERROR
            # ---------------------------------

            self.error_x, self.error_y = (
                self.camera.calculate_error(
                    self.beacon.x,
                    self.beacon.y
                )
            )

            # ---------------------------------
            # CONTROLLER CALCULATES MOVEMENT
            # ---------------------------------

            move_x, move_y = (
                self.controller.calculate_movement(
                    self.error_x,
                    self.error_y
                )
            )

            # ---------------------------------
            # MOVE CAMERA
            # ---------------------------------

            self.camera.move(
                move_x,
                move_y,
                self.width(),
                self.height()
            )


        else:

            # ---------------------------------
            # CAMERA SEARCH MODE
            # ---------------------------------

            self.camera.search(
                self.width(),
                self.height()
            )

        # ---------------------------------
        # RECALCULATE ERROR
        # AFTER CAMERA MOVEMENT
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

            # ---------------------------------
            # IF TARGET IS NOT VISIBLE
            # ---------------------------------

            if not self.target_visible:

                self.state = "SEARCHING"


            else:

                # ---------------------------------
                # CHECK IF TARGET IS LOCKED
                # ---------------------------------

                if (
                    abs(self.error_x) <= self.lock_threshold
                    and
                    abs(self.error_y) <= self.lock_threshold
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
        # DRAW BACKGROUND
        # ---------------------------------

        painter.fillRect(
            self.rect(),
            QColor(15, 20, 35)
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

            # Purple color for locked

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
            QColor(0, 200, 255)
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
        # DRAW BEACON
        # ---------------------------------

        painter.setBrush(
            QColor(255, 60, 60)
        )

        painter.setPen(
            Qt.NoPen
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
                self.beacon.radius * 2 + 14
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

        painter.end()
        def keyPressEvent(self, event):

                 # SPACE = Pause / Start
             if event.key() == Qt.Key_Space:

                 self.is_running = not self.is_running

                 if self.is_running:
                     print("Simulation Started")
                 else:
                     print("Simulation Paused")


                   # R = Reset simulation
             elif event.key() == Qt.Key_R:

                    # Reset beacon
                  self.beacon.x = 300
                  self.beacon.y = 200

                  # Reset beacon velocity
                  self.beacon.vx = 1.0
                  self.beacon.vy = 0.8

                  # Reset camera
                  self.camera.x = 250
                  self.camera.y = 150

                    # Reset state
                  self.state = "SEARCHING"

                  self.target_visible = False
                  self.previous_visible = False

                   # Reset error
                  self.error_x = 0.0
                  self.error_y = 0.0

                  self.state_counter = 0

                  # Reset running state
                  self.is_running = True

                  self.update()

                  print("Simulation Reset")
import math
import random

from PySide6.QtGui import QColor, QPen
from PySide6.QtCore import Qt


class OceanEnvironment:

    def __init__(self):

        # Animation time
        self.time = 0.0

        # Create distant clouds
        self.clouds = []

        for _ in range(8):

            self.clouds.append({

                "x": random.randint(0, 1400),
                "y": random.randint(40, 250),

                "speed": random.uniform(
                    0.1,
                    0.4
                ),

                "size": random.randint(
                    40,
                    100
                )
            })


    def update(self, world_width):

        # Update animation
        self.time += 0.03

        # Move clouds slowly
        for cloud in self.clouds:

            cloud["x"] += cloud["speed"]

            if cloud["x"] > world_width + 150:

                cloud["x"] = -150


    def draw(self, painter, width, height):

        # =================================
        # SKY GRADIENT EFFECT
        # =================================

        horizon = int(height * 0.45)

        # Draw sky using horizontal lines

        for y in range(horizon):

            ratio = y / max(1, horizon)

            r = int(
                70 + ratio * 100
            )

            g = int(
                140 + ratio * 80
            )

            b = int(
                220 + ratio * 20
            )

            painter.setPen(
                QColor(r, g, b)
            )

            painter.drawLine(
                0,
                y,
                width,
                y
            )

        # =================================
        # DRAW CLOUDS
        # =================================

        painter.setPen(Qt.NoPen)

        painter.setBrush(
            QColor(
                255,
                255,
                255,
                120
            )
        )

        for cloud in self.clouds:

            x = cloud["x"]
            y = cloud["y"]
            size = cloud["size"]

            painter.drawEllipse(
                int(x),
                int(y),
                size,
                int(size * 0.5)
            )

            painter.drawEllipse(
                int(x + size * 0.3),
                int(y - size * 0.2),
                size,
                int(size * 0.6)
            )

            painter.drawEllipse(
                int(x + size * 0.6),
                int(y),
                size,
                int(size * 0.5)
            )

        # =================================
        # DRAW OCEAN
        # =================================

        painter.fillRect(

            0,
            horizon,

            width,
            height - horizon,

            QColor(
                15,
                90,
                150
            )
        )

        # =================================
        # OCEAN WAVES
        # =================================

        painter.setPen(
            QPen(
                QColor(
                    180,
                    230,
                    255,
                    120
                ),
                2
            )
        )

        # Multiple wave lines

        for row in range(12):

            y = horizon + row * 35

            points = []

            for x in range(
                0,
                width,
                10
            ):

                wave_y = (

                    y

                    + math.sin(
                        x * 0.03
                        + self.time * 4
                        + row
                    )

                    * 6

                )

                points.append(
                    (x, wave_y)
                )

            for i in range(
                len(points) - 1
            ):

                painter.drawLine(

                    int(points[i][0]),
                    int(points[i][1]),

                    int(points[i + 1][0]),
                    int(points[i + 1][1])

                )

        # =================================
        # HORIZON LINE
        # =================================

        horizon_pen = QPen(
            QColor(
                220,
                240,
                255
            )
        )

        horizon_pen.setWidth(2)

        painter.setPen(
            horizon_pen
        )

        painter.drawLine(

            0,
            horizon,

            width,
            horizon

        )


    def draw_target(

        self,
        painter,

        x,
        y,

        animation_time

    ):

        # =================================
        # DRAW UAV / BEACON TARGET
        # =================================

        # Blinking light

        pulse = (

            math.sin(
                animation_time * 6
            )

            + 1

        ) / 2

        glow_size = (
            20
            + pulse * 15
        )

        # Glow

        painter.setPen(
            Qt.NoPen
        )

        painter.setBrush(

            QColor(

                255,
                60,
                40,

                int(
                    40
                    + pulse * 120
                )

            )

        )

        painter.drawEllipse(

            int(x - glow_size),
            int(y - glow_size),

            int(glow_size * 2),
            int(glow_size * 2)

        )

        # UAV wings

        painter.setPen(

            QPen(
                QColor(
                    50,
                    50,
                    60
                ),
                4
            )

        )

        painter.drawLine(

            int(x - 30),
            int(y),

            int(x + 30),
            int(y)

        )

        # UAV body

        painter.setBrush(
            QColor(
                80,
                80,
                90
            )
        )

        painter.drawEllipse(

            int(x - 10),
            int(y - 6),

            20,
            12

        )

        # Blinking beacon light

        painter.setBrush(

            QColor(
                255,
                int(80 + pulse * 150),
                40
            )

        )

        painter.drawEllipse(

            int(x - 7),
            int(y - 7),

            14,
            14

        )
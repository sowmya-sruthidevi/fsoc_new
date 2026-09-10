import random


class Beacon:

    def __init__(self, x, y, radius=12):

        self.x = float(x)
        self.y = float(y)

        self.radius = radius

        # Normal movement velocity
        self.vx = 0.4
        self.vy = 0.3

        # Counter for direction changes
        self.disturbance_counter = 0

        # Counter for sudden escape movement
        self.escape_counter = 0


    def update(self, width, height):

        # -------------------------
        # NORMAL MOVEMENT
        # -------------------------

        self.x += self.vx
        self.y += self.vy


        # -------------------------
        # RANDOM DISTURBANCE
        # -------------------------

        self.disturbance_counter += 1

        if self.disturbance_counter >= 120:

            # Change direction and speed
            self.vx += random.uniform(-2.0, 2.0)
            self.vy += random.uniform(-2.0, 2.0)

            # Keep normal speed within limits
            self.vx = max(-5, min(5, self.vx))
            self.vy = max(-5, min(5, self.vy))

            self.disturbance_counter = 0


        # -------------------------
        # OCCASIONAL FAST MOVEMENT
        # Helps test TARGET LOST
        # -------------------------

        self.escape_counter += 1

        if self.escape_counter >= 300:

            # Sudden random direction
            angle_x = random.choice([-1, 1])
            angle_y = random.choice([-1, 1])

            # Fast movement
            self.vx = random.uniform(5, 8) * angle_x
            self.vy = random.uniform(4, 7) * angle_y

            self.escape_counter = 0


        # -------------------------
        # LEFT / RIGHT WALL
        # -------------------------

        if self.x - self.radius <= 0:

            self.x = self.radius
            self.vx = abs(self.vx)

        elif self.x + self.radius >= width:

            self.x = width - self.radius
            self.vx = -abs(self.vx)


        # -------------------------
        # TOP / BOTTOM WALL
        # -------------------------

        if self.y - self.radius <= 0:

            self.y = self.radius
            self.vy = abs(self.vy)

        elif self.y + self.radius >= height:

            self.y = height - self.radius
            self.vy = -abs(self.vy)
class TrackingController:

    def __init__(self):

        # Camera response speed
        self.kp = 0.12

        # Maximum camera movement
        # per simulation update
        self.max_speed = 4.0


    def calculate_movement(
        self,
        error_x,
        error_y
    ):

        # Proportional controller

        move_x = error_x * self.kp
        move_y = error_y * self.kp

        # Limit maximum X movement

        move_x = max(
            -self.max_speed,
            min(
                self.max_speed,
                move_x
            )
        )

        # Limit maximum Y movement

        move_y = max(
            -self.max_speed,
            min(
                self.max_speed,
                move_y
            )
        )

        return move_x, move_y
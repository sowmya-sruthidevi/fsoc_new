class VirtualCamera:

    def __init__(self, x, y, width=500, height=350):

        # Camera top-left position
        self.x = float(x)
        self.y = float(y)

        # Camera Field of View
        self.width = width
        self.height = height

        # Search movement speed
        self.search_speed = 5.0

        # Horizontal search direction
        # 1 = right, -1 = left
        self.search_direction = 1

        # Vertical search direction
        # 1 = down, -1 = up
        self.search_vertical_direction = 1

        # Continuous vertical movement speed
        self.vertical_speed = 1.5


    def get_center(self):
        """Return camera center."""

        center_x = self.x + self.width / 2
        center_y = self.y + self.height / 2

        return center_x, center_y


    def is_target_visible(self, target_x, target_y):
        """Check whether target is inside camera FOV."""

        inside_x = (
            self.x <= target_x <= self.x + self.width
        )

        inside_y = (
            self.y <= target_y <= self.y + self.height
        )

        return inside_x and inside_y


    def calculate_error(self, target_x, target_y):
        """
        Calculate error between target
        and camera center.
        """

        center_x, center_y = self.get_center()

        error_x = target_x - center_x
        error_y = target_y - center_y

        return error_x, error_y


    def move(
        self,
        move_x,
        move_y,
        world_width,
        world_height
    ):
        """
        Move camera according to controller output
        while keeping camera inside the world.
        """

        # Move camera
        self.x += move_x
        self.y += move_y

        # Maximum allowed camera positions
        max_x = max(
            0,
            world_width - self.width
        )

        max_y = max(
            0,
            world_height - self.height
        )

        # Keep camera inside horizontal boundaries
        self.x = max(
            0,
            min(self.x, max_x)
        )

        # Keep camera inside vertical boundaries
        self.y = max(
            0,
            min(self.y, max_y)
        )


    def search(self, world_width, world_height):
        """
        Smooth diagonal search pattern.

        Camera moves:
        Left ↔ Right
        while continuously moving
        Up ↕ Down
        """

        # Horizontal movement
        self.x += (
            self.search_speed
            * self.search_direction
        )

        # Continuous vertical movement
        self.y += (
            self.vertical_speed
            * self.search_vertical_direction
        )

        # Maximum positions
        max_x = max(
            0,
            world_width - self.width
        )

        max_y = max(
            0,
            world_height - self.height
        )

        # RIGHT boundary
        if self.x >= max_x:

            self.x = max_x

            # Reverse horizontal direction
            self.search_direction = -1

        # LEFT boundary
        elif self.x <= 0:

            self.x = 0

            # Reverse horizontal direction
            self.search_direction = 1


        # BOTTOM boundary
        if self.y >= max_y:

            self.y = max_y

            # Reverse vertical direction
            self.search_vertical_direction = -1

        # TOP boundary
        elif self.y <= 0:

            self.y = 0

            # Reverse vertical direction
            self.search_vertical_direction = 1
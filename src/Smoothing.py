import time


class Smoothing:
    def __init__(self, steering_speed: float = 4.0, speed_speed: float = 0.08):
        self.current_angle = 0.0
        self.current_speed = 0.0
        self.steering_speed = steering_speed
        self.speed_speed = speed_speed
        self.last_time_steering = time.time()
        self.last_time_speed = time.time()
        self.last_delta_steering = 0.0
        self.last_delta_speed = 0.0

    def set_speed_speed(self, speed_speed: float):
        """
        Set the speed of changing the speed factor.
        """
        self.speed_speed = speed_speed

    def set_steering_speed(self, steering_speed: float):
        """
        Set the speed of changing the steering angle.
        """
        self.steering_speed = steering_speed

    def calculate_delta_steering(self) -> float:
        now = time.time()
        self.last_delta_steering = now - self.last_time_steering
        self.last_time_steering = now
        return self.last_delta_steering

    def calculate_delta_speed(self) -> float:
        now = time.time()
        self.last_delta_speed = now - self.last_time_speed
        self.last_time_speed = now
        return self.last_delta_speed

    def smooth_steering(self, wanted_angle: float) -> float:
        """
        Smoothly move the steering angle towards the wanted angle, taking into account the velocity.
        """
        step = (
            self.steering_speed
            * self.calculate_delta_steering()
            * (1 - abs(self.current_speed))
        )
        self.current_angle = self.move_toward(self.current_angle, wanted_angle, step)
        return self.current_angle

    def smooth_speed(self, wanted_speed: float) -> float:
        """
        Smoothly change the speed towards the wanted speed.
        """
        step = self.speed_speed * self.calculate_delta_speed()
        self.current_speed = self.move_toward(self.current_speed, wanted_speed, step)
        return self.current_speed

    def move_toward(self, current: float, target: float, step: float) -> float:
        if abs(target - current) <= step:
            return target
        return current + step * (1 if target > current else -1)

    def get_current_steering(self) -> float:
        return self.current_angle

    def get_current_speed(self) -> float:
        return self.current_speed

    def get_last_delta_steering(self) -> float:
        return self.last_delta_steering

    def get_last_delta_speed(self) -> float:
        return self.last_delta_speed

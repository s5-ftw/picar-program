import time

class Smoothing:
    def __init__(self, steering_speed: float = 1.0):
        self.current_angle = 0.0
        self.current_speed = 0.0
        self.steering_speed = steering_speed
        self.last_time_steering = time.time()
        self.last_time_speed = time.time()

    def get_delta_steering(self) -> float:
        now = time.time()
        delta = now - self.last_time_steering
        self.last_time_steering = now
        return delta
    
    def get_delta_speed(self) -> float:
        now = time.time()
        delta = now - self.last_time_speed
        self.last_time_speed = now
        return delta

    def smooth_steering(self, wanted_angle: float, velocity: float) -> float:
        step = self.steering_speed * self.get_delta_steering() * (1 - abs(velocity))
        self.current_angle = self.move_toward(self.current_angle, wanted_angle, step)
        return self.current_angle
    
    def smooth_speed(self, wanted_speed: float) -> float:
        step = self.steering_speed * self.get_delta_speed()
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
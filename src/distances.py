import numpy as np

class Distances:
    def __init__(self):
        self.distance_traveled = 0.0
        
    def update_distance(self, speed: float, delta_time: float) -> float:
        self.distance_traveled += self.function_turbo_calcul_de_chat_martin(speed, delta_time)
        return self.distance_traveled

    def get_distance_traveled(self):
        return self.distance_traveled
    
    def reset_distance(self):
        self.distance_traveled = 0.0
    
    def function_turbo_calcul_de_chat_martin(self, speed: float, delta_time: float) -> float:
        return 2.7717 * delta_time * np.exp(6.3368 * speed)

from enum import Enum

from api import (
    line_follower_read,
    measure_distance,
    set_motor_speed,
    set_steering,
)
from Smoothing import Smoothing

AVOID_DISTANCE = 10

SPEED_FAST = 0.25
SPEED_SLOW = 0.15

STEER_SHARP = 1.0
STEER_SMOOTH = 0.5
STEER_STRAIGHT = 0.0


class states(Enum):
    START = 0
    FOLLOWING = 1
    AVOIDING = 2
    STOPPED = 3


class LineFollower:
    def __init__(
        self,
    ):
        pass

    def reaction(
        self,
    ) -> tuple[float, float]:
        res = line_follower_read()
        # print(f"line follower: {res}")

        steer: float = STEER_STRAIGHT
        speed: float = SPEED_FAST

        # get steering
        if res[0] == 1:
            steer = -STEER_SHARP
        elif res[4] == 1:
            steer = STEER_SHARP
        elif res[1] == 1:
            steer = -STEER_SMOOTH
        elif res[3] == 1:
            steer = STEER_SMOOTH
        elif res[2] == 1:
            steer = STEER_STRAIGHT

        # get speed
        if abs(steer) > STEER_SMOOTH:
            speed = SPEED_SLOW
        else:
            speed = SPEED_FAST

        return (steer, speed)


class Avoider:
    finished_avoid = False

    class states(Enum):
        BACKUP = 0
        IDLE = 1
        TRUN_RIGHT = 2
        GOING_FORWARD = 3
        RETURNING = 4
        FIND_LINE = 5

    current_state: states

    def __init__(self, smooth: Smoothing):
        self.current_state = self.states.BACKUP
        self.smoothing = smooth

    def should_avoid(
        self,
    ) -> bool:
        distance = measure_distance()
        if distance < AVOID_DISTANCE:
            return True
        else:
            return False

    def avoid(
        self,
    ) -> tuple[float, float]:

        self.finished_avoid = False

        match self.current_state:
            case self.states.BACKUP:
                steer = STEER_STRAIGHT
                speed = -SPEED_SLOW

                if measure_distance() >= AVOID_DISTANCE:
                    self.current_state = self.states.IDLE

            case self.states.IDLE:
                steer = STEER_STRAIGHT
                speed = 0
                if self.smoothing.get_current_speed() == 0:
                    self.current_state = self.states.TRUN_RIGHT

            case self.states.TRUN_RIGHT:
                steer = STEER_SHARP
                speed = SPEED_SLOW
                # TODO: Will need to calculate what is the actual angle of the car
                if self.smoothing.get_current_steering() >= STEER_SHARP:
                    self.current_state = self.states.GOING_FORWARD

            case self.states.GOING_FORWARD:
                steer = STEER_STRAIGHT
                speed = SPEED_SLOW
                # TODO: Calculate the actual distance traveled by the car, to see if we passed the obstacle
                self.current_state = self.states.RETURNING

            case self.states.RETURNING:
                steer = -STEER_SHARP
                speed = SPEED_SLOW
                # TODO: Will need to calculate what is the actual angle of the car
                if self.smoothing.get_current_steering() <= -STEER_SHARP:
                    self.current_state = self.states.FIND_LINE

            case self.states.FIND_LINE:
                steer = STEER_STRAIGHT
                speed = SPEED_SLOW
                if any(line_follower_read()):
                    self.current_state = self.states.BACKUP
                    self.finished_avoid = True

        return (steer, speed)

    def is_finished(
        self,
    ) -> bool:
        return self.finished_avoid


class machine:
    def __init__(
        self,
        state: states,
    ):
        self.state = state
        self.smoothing = Smoothing()
        self.line_follower = LineFollower()
        self.avoider = Avoider(self.smoothing)

    def loop(
        self,
    ):
        # print(f"car state: {self.state.name}")

        if self.state == states.START:
            self.start_state()

        elif self.state == states.FOLLOWING:
            self.following_state()

        elif self.state == states.AVOIDING:
            self.avoid_state()

        elif self.state == states.STOPPED:
            self.stop_state()

        return

    def start_state(
        self,
    ) -> None:
        self.state = states.FOLLOWING

    def following_state(
        self,
    ) -> None:
        steer, speed = self.line_follower.reaction()
        print(f"steer: {steer}, speed: {speed}")
        set_steering(str(self.smoothing.smooth_steering(steer, speed)))
        set_motor_speed(str(self.smoothing.smooth_speed(speed)))
        if self.avoider.should_avoid():
            self.state = states.AVOIDING

    def avoid_state(
        self,
    ) -> None:
        steer, speed = self.avoider.avoid()
        print(f"steer: {steer}, speed: {speed}")
        set_steering(str(self.smoothing.smooth_steering(steer, speed)))
        set_motor_speed(str(self.smoothing.smooth_speed(speed)))
        if self.avoider.is_finished():
            self.state = states.FOLLOWING

    def stop_state(
        self,
    ) -> None:
        set_steering("0")
        set_motor_speed("0")
        self.state = states.STOPPED


def main():
    car = machine(states.START)
    while True:
        try:
            car.loop()
        except KeyboardInterrupt:
            # Code to run when Ctrl+C is pressed
            print("\nKeyboardInterrupt caught. Performing cleanup...")
            car.stop_state()
            break


if __name__ == "__main__":
    main()

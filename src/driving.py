from enum import Enum
from typing import Callable

from api import (
    line_follower_read,
    measure_distance,
    set_motor_speed,
    set_steering,
)

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

        steer = STEER_STRAIGHT
        speed = SPEED_FAST

        # get steering
        if res[0] == 1:
            steer = -STEER_SHARP
        elif res[4] == 1:
            steer = STEER_SHARP
        elif res[1] == 1:
            steer = -STEER_SMOOTH
        elif res[3] == 1:
            steer = STEER_SMOOTH
        else:
            steer = STEER_STRAIGHT

        # get speed
        if abs(steer) > STEER_SMOOTH:
            speed = SPEED_SLOW
        else:
            speed = SPEED_FAST

        return (steer, speed)


class Avoider:
    def __init__(
        self,
    ):
        pass

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
    ):
        pass


class machine:
    def __init__(
        self,
        state: states,
    ):
        self.state = state
        self.line_follower = LineFollower()
        self.avoider = Avoider()

    def loop(
        self,
    ):
        print(f"car state: {self.state.name}")

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
        set_steering(str(steer))
        set_motor_speed(str(speed))
        if self.avoider.should_avoid():
            self.state = states.AVOIDING

    def avoid_state(
        self,
    ) -> None:
        self.avoider.avoid()
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

from enum import Enum
from typing import Callable

from api import (
    line_follower_read,
    measure_distance,
    set_motor_speed,
    set_steering,
)

AVOID_DISTANCE = 10


class states(Enum):
    START = 0
    FOLLOWING = 1
    AVOIDING = 2


class LineFollower:
    SHARP = 1
    SMOOTH = 0.5
    STRAIGHT = 0

    def __init__(
        self,
    ):
        pass

    def reaction(
        self,
    ):
        res = line_follower_read()
        print(f"line follower: {res}")

        if res[0] == 1:
            react = -self.SHARP
        elif res[4] == 1:
            react = self.SHARP
        elif res[1] == 1:
            react = self.SMOOTH
        elif res[3] == 1:
            react = self.SMOOTH
        else:
            react = self.STRAIGHT

        return react


class Avoider:
    def __init__(
        self,
    ):
        pass

    def should_avoid(
        self,
    ):
        distance = measure_distance()
        if distance < AVOID_DISTANCE:
            return 1
        else:
            return 0

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

    def start_state(
        self,
    ):
        self.state = states.FOLLOWING

    def following_state(
        self,
    ):
        reaction = self.line_follower.reaction()
        set_steering(reaction)
        if self.avoider.should_avoid():
            self.state = states.AVOIDING

    def avoid_state(
        self,
    ):
        self.avoider.avoid()
        self.state = states.FOLLOWING


def main():
    car = machine(states.START)
    while True:
        car.loop()


if __name__ == "__main__":
    main()

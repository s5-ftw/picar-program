import time
from collections import deque
from enum import Enum

from api import (
    line_follower_read,
    measure_distance,
    set_motor_speed,
    set_steering,
)
from distances import Distances
from Smoothing import Smoothing

DETECT_OBJECT_TO_AVOID = 25
DISTANCE_TO_STOP_AT_OBJECT = 10
DISTANCE_BACKING_UP_TO = 25
TURNING_DISTANCE_OUTWARD_TRAVELED = 18
TURNING_DISTANCE_INWARD_TRAVELED = 30
STRAIGHT_DISTANCE_TRAVELED = 25

SPEED_FAST = 0.35
SPEED_SLOW = 0.28
SPEED_VERY_SLOW = 0.12

STEER_SHARP = 1.0
STEER_SMOOTH = 0.25
STEER_STRAIGHT = 0.0

DEFAULT_SPEED_SPEED = 0.08

TIME_BEFORE_CAN_STOP = 5


class LineFollower:
    def __init__(
        self,
    ):
        self.steer = STEER_STRAIGHT
        self.speed: float = SPEED_FAST
        self.stop = False

    @staticmethod
    def detect_t(res: list[int] | None = None) -> bool:
        """
        Return True if all line follower sensors are active.
        """
        res = res if res is not None else line_follower_read()

        if res == [1, 1, 1, 1, 1]:
            return True

        return False

    def reaction(
        self,
    ) -> tuple[float, float]:
        res = line_follower_read()
        # print(f"line follower: {res}")

        if self.detect_t(res):
            self.stop = True
            return (self.steer, self.speed)

        # get steering
        if res[0] == 1:
            self.steer = -STEER_SHARP
        elif res[4] == 1:
            self.steer = STEER_SHARP
        elif res[1] == 1:
            self.steer = -STEER_SMOOTH
        elif res[3] == 1:
            self.steer = STEER_SMOOTH
        elif res[2] == 1:
            self.steer = STEER_STRAIGHT

        # get speed
        if abs(self.steer) > STEER_SMOOTH:
            self.speed = SPEED_SLOW
        else:
            self.speed = SPEED_FAST

        return (self.steer, self.speed)


class Avoider:
    finished_avoid = False
    array_size = 5

    class states(Enum):
        BACKUP = 0
        IDLE = 1
        TURN_RIGHT = 2
        GOING_FORWARD = 3
        RETURNING = 4
        FIND_LINE = 5
        STOP_AT_OBJECT = 6
        ADJUST_TO_OBJECT = 7

    current_state: states
    finished_avoid: bool

    def __init__(self, smooth: Smoothing):
        self.current_state = self.states.STOP_AT_OBJECT
        self.smoothing = smooth
        self.distances = Distances()
        self.finished_avoid = False
        self.adjust_distance_precision = 0.0

    def should_avoid(self) -> bool:
        distance = measure_distance()
        if distance < DETECT_OBJECT_TO_AVOID:
            return True
        else:
            return False

    def avoid(self) -> tuple[float, float]:

        self.finished_avoid = False

        # print(f"car state: {self.current_state.name}")

        match self.current_state:
            case self.states.STOP_AT_OBJECT:
                self.smoothing.set_speed_speed(
                    0.2
                )  # TODO maybe make that not run each time
                steer = STEER_STRAIGHT
                speed = SPEED_SLOW

                if self.smoothing.get_current_speed() < SPEED_VERY_SLOW:
                    self.smoothing.set_speed_speed(
                        1
                    )  # TODO maybe make that not run each time
                    self.current_state = self.states.ADJUST_TO_OBJECT

            case self.states.ADJUST_TO_OBJECT:
                steer = STEER_STRAIGHT
                speed = SPEED_VERY_SLOW

                if (
                    abs(DISTANCE_TO_STOP_AT_OBJECT - measure_distance())
                    < self.adjust_distance_precision
                ):
                    # stop at the right place
                    self.smoothing.current_speed = 0
                    set_motor_speed(0)

                    # reset speed speed
                    self.smoothing.set_speed_speed(
                        0.2
                    )  # TODO maybe make that not run each time
                    self.current_state = self.states.IDLE

                elif (
                    DISTANCE_TO_STOP_AT_OBJECT - measure_distance()
                    < -self.adjust_distance_precision
                ):
                    speed = -SPEED_VERY_SLOW

            case self.states.BACKUP:
                steer = STEER_STRAIGHT
                speed = -SPEED_SLOW

                if measure_distance() >= DISTANCE_BACKING_UP_TO:
                    self.current_state = self.states.IDLE

            case self.states.IDLE:
                steer = STEER_STRAIGHT
                speed = 0
                if self.smoothing.get_current_speed() == 0:
                    self.current_state = self.states.TURN_RIGHT
                    self.distances.reset_distance()

            case self.states.TURN_RIGHT:
                steer = STEER_SHARP
                speed = SPEED_SLOW
                distance = self.distances.update_distance(
                    self.smoothing.get_current_speed(),
                    self.smoothing.get_last_delta_speed(),
                )

                print(f"TURN RIGHT distance: {distance}")

                if distance >= TURNING_DISTANCE_OUTWARD_TRAVELED:
                    self.current_state = self.states.GOING_FORWARD
                    self.distances.reset_distance()

            case self.states.GOING_FORWARD:
                steer = STEER_STRAIGHT
                speed = SPEED_SLOW

                if (
                    self.distances.update_distance(
                        self.smoothing.get_current_speed(),
                        self.smoothing.get_last_delta_speed(),
                    )
                    >= STRAIGHT_DISTANCE_TRAVELED
                ):
                    self.current_state = self.states.RETURNING
                    self.distances.reset_distance()

            case self.states.RETURNING:
                steer = -STEER_SHARP
                speed = SPEED_SLOW

                if (
                    self.distances.update_distance(
                        self.smoothing.get_current_speed(),
                        self.smoothing.get_last_delta_speed(),
                    )
                    >= TURNING_DISTANCE_INWARD_TRAVELED
                ):
                    self.current_state = self.states.FIND_LINE

            case self.states.FIND_LINE:
                steer = STEER_STRAIGHT
                speed = SPEED_SLOW
                if any(line_follower_read()):
                    self.finished_avoid = True

        return (steer, speed)

    def reset(self) -> None:
        self.smoothing.set_speed_speed(DEFAULT_SPEED_SPEED)
        self.distances.reset_distance()
        self.distance_array.clear()
        self.current_state = self.states.STOP_AT_OBJECT

    def is_finished(
        self,
    ) -> bool:
        return self.finished_avoid


class machine:
    class states(Enum):
        START = 0
        FOLLOWING = 1
        AVOIDING = 2
        STOPPED = 3

    def __init__(self):
        self.state = self.states.START
        self.smoothing = Smoothing(speed_speed=2.0)
        self.line_follower = LineFollower()
        self.avoider = Avoider(self.smoothing)

    def loop(self):

        if self.state == self.states.START:
            self.start_state()

        elif self.state == self.states.FOLLOWING:
            self.following_state()

        elif self.state == self.states.AVOIDING:
            self.avoid_state()

        elif self.state == self.states.STOPPED:
            self.stop_state()

        return

    def start_state(self) -> None:
        """
        while we detect the T, go forward.
        When we detect no T, follow
        """

        if self.line_follower.detect_t():
            set_steering(self.smoothing.smooth_steering(STEER_STRAIGHT))
            self.smoothing.smooth_speed(SPEED_FAST)
        else:
            self.state = self.states.FOLLOWING
            self.start_T_time = time.time()
            self.smoothing.set_speed_speed(DEFAULT_SPEED_SPEED)

    def following_state(self) -> None:
        steer, speed = self.line_follower.reaction()
        # print(f"steer: {steer}, speed: {speed}")
        set_steering(self.smoothing.smooth_steering(steer))
        set_motor_speed(self.smoothing.smooth_speed(speed))
        if self.avoider.should_avoid():
            print("following: going to avoid")
            self.state = self.states.AVOIDING
            self.avoider.reset()
        if self.line_follower.stop:
            if time.time() - self.start_T_time > TIME_BEFORE_CAN_STOP:
                self.state = self.states.STOPPED
            else:
                self.line_follower.stop = False

    def avoid_state(self) -> None:
        steer, speed = self.avoider.avoid()
        # print(f"steer: {steer}, speed: {speed}")
        set_steering(self.smoothing.smooth_steering(steer))
        set_motor_speed(self.smoothing.smooth_speed(speed))
        if self.avoider.is_finished():
            print("avoiding: going to follow")
            self.state = self.states.FOLLOWING

    def stop_state(self) -> None:
        self.smoothing.set_speed_speed(0.2)
        set_steering(self.smoothing.smooth_steering(STEER_STRAIGHT))
        set_motor_speed(self.smoothing.smooth_speed(0.0))
        self.state = self.states.STOPPED


def main():
    car = machine()
    while True:
        try:
            car.loop()
        except KeyboardInterrupt:
            # Code to run when Ctrl+C is pressed
            print("\nKeyboardInterrupt caught. Performing cleanup...")

            set_motor_speed(0.0)
            set_steering(STEER_STRAIGHT)

            break


if __name__ == "__main__":
    main()

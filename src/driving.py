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

DETECT_OBJECT_TO_AVOID = 30
DISTANCE_TO_STOP_AT_OBJECT = 18
DISTANCE_BACKING_UP_TO = 30
TURNING_DISTANCE_OUTWARD_TRAVELED = 25
TURNING_DISTANCE_INWARD_TRAVELED = 25
STRAIGHT_DISTANCE_TRAVELED = 40


# Original speed = 0.35
SPEED_FAST = 0.27
SPEED_SLOW = 0.23 # 0.28
SPEED_VERY_SLOW = 0.18

STEER_SHARP = 1.0
STEER_SMOOTH = 0.25
STEER_STRAIGHT = 0.0
STEER_SMALL = 0.5
STEER_VERY_SMALL_FINDING_LINE = 0.2

DEFAULT_SPEED_SPEED = 0.08

TIME_BEFORE_CAN_STOP = 5

TIME_ALLOWED_TO_LOST_LINE = 1.0

#Positive steer is right, negative steer is left
AVOID_TURN_DIRECTION = -1.3


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
        
        if sum(res) >= 3:
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
    
    def lostLine(self,) -> bool:
        res = line_follower_read()
        return res == [0, 0, 0, 0, 0]
    
    def getSteering(self,) -> float:
        return self.steer


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

    def __init__(self, smooth: Smoothing, line_follow: LineFollower):
        self.current_state = self.states.STOP_AT_OBJECT
        self.smoothing = smooth
        self.line_follower = line_follow
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
                self.smoothing.set_speed_speed(0.2)
                steer, speed = self.line_follower.reaction()
                # steer = STEER_STRAIGHT
                speed = SPEED_VERY_SLOW

                if measure_distance() < DISTANCE_TO_STOP_AT_OBJECT:
                    self.current_state = self.states.BACKUP

            case self.states.ADJUST_TO_OBJECT:
                steer = STEER_STRAIGHT
                speed = 0

                if self.smoothing.get_current_speed() == 0:
                    self.current_state = self.states.BACKUP

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
                steer = STEER_SHARP * AVOID_TURN_DIRECTION
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
                steer = -STEER_SMALL * AVOID_TURN_DIRECTION
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
                steer = -STEER_SHARP * AVOID_TURN_DIRECTION
                speed = SPEED_SLOW

                if (
                    self.distances.update_distance(
                        self.smoothing.get_current_speed(),
                        self.smoothing.get_last_delta_speed(),
                    )
                    >= TURNING_DISTANCE_INWARD_TRAVELED
                ):
                    self.current_state = self.states.FIND_LINE
                    
                if any(line_follower_read()):
                    self.finished_avoid = True

            case self.states.FIND_LINE:
                steer = STEER_VERY_SMALL_FINDING_LINE * AVOID_TURN_DIRECTION
                speed = SPEED_SLOW
                if any(line_follower_read()):
                    self.finished_avoid = True

        return (steer, speed)

    def reset(self) -> None:
        self.smoothing.set_speed_speed(DEFAULT_SPEED_SPEED)
        self.distances.reset_distance()
        
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
        LOST_LINE = 4
        BACK_UP_TO_LINE = 5
        IDLE_BEFORE_FOLLOWING = 6

    def __init__(self):
        self.state = self.states.START
        self.smoothing = Smoothing(speed_speed=2.0)
        self.line_follower = LineFollower()
        self.avoider = Avoider(self.smoothing)
        self.lost_line_start = None
        self.lost_line_stering = 0.0

    def loop(self):
        print(f"State of car: {self.state}")
        if self.state == self.states.START:
            self.start_state()

        elif self.state == self.states.FOLLOWING:
            self.following_state()

        elif self.state == self.states.AVOIDING:
            self.avoid_state()

        elif self.state == self.states.STOPPED:
            self.stop_state()
            
        elif self.state == self.states.LOST_LINE:
            self.lost_line_state()
            
        elif self.state == self.states.BACK_UP_TO_LINE:
            self.back_up_to_line_state()
        
        elif self.state == self.states.IDLE_BEFORE_FOLLOWING:
            self.idle_before_following_state()

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
        lost_line = self.line_follower.lostLine()
        
        if lost_line:
            if self.lost_line_start is None:
                # start timer
                self.lost_line_start = time.time()

            elif time.time() - self.lost_line_start > TIME_ALLOWED_TO_LOST_LINE:
                self.state = self.states.LOST_LINE
                self.lost_line_start = None

        else:
            # reset timer if line is found again
            self.lost_line_start = None
            
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
        
    def lost_line_state(self) -> None:
        #set_steering(self.smoothing.smooth_steering(STEER_VERY_SMALL_FINDING_LINE))
        set_motor_speed(self.smoothing.smooth_speed(0.0))
        self.lost_line_stering = -self.line_follower.getSteering()
        
        if any(line_follower_read()):
            self.state = self.states.FOLLOWING
            self.lost_line_start = None
        
        if self.smoothing.get_current_speed() <= 0:
            self.state = self.states.BACK_UP_TO_LINE
            self.lost_line_start = None
            
    def back_up_to_line_state(self) -> None:
        set_steering(self.smoothing.smooth_steering(self.lost_line_stering))
        set_motor_speed(self.smoothing.smooth_speed(-SPEED_SLOW))
        
        if any(line_follower_read()):
            self.state = self.states.IDLE_BEFORE_FOLLOWING
            self.lost_line_start = None
            
    def idle_before_following_state(self) -> None:
        set_steering(self.smoothing.smooth_steering(self.lost_line_stering))
        set_motor_speed(self.smoothing.smooth_speed(0.0))
        
        if any(line_follower_read()):
            self.state = self.states.FOLLOWING
            self.lost_line_start = None


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

import sys
import time

import RPi.GPIO as GPIO

import utils
import utils.PCF8591
from utils.back_wheels import Back_Wheels
from utils.front_wheels import Front_Wheels
from utils.SunFounder_Line_Follower.Line_Follower import Line_Follower
from utils.SunFounder_PCA9685 import PCA9685, Servo

GPIO.setmode(GPIO.BCM)

_TRIG = 12
_ECHO = 16
_LINE_FOLLOWER_REFERENCE = [20, 20, 20, 20, 20]


class _UltrasonicSensor:
    def __init__(self, trig_pin, echo_pin):
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)

        self.waitTime = 0.05

    def calibrate(self):
        GPIO.output(self.trig_pin, False)
        print("Calibration.....")
        time.sleep(2)
        print("Calibration complete")

    def measure_distance(self):
        GPIO.output(self.trig_pin, True)
        GPIO.output(self.trig_pin, False)

        pulse_start, pulse_end = 0, 0

        while GPIO.input(self.echo_pin) == 0:
            pulse_start = time.time()

        while GPIO.input(self.echo_pin) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration * 16666

        distance = round(distance, 2)

        if distance <= 3:
            distance = 0
            raise ValueError("Distance too close")

        return distance


_distance_sensor = _UltrasonicSensor(_TRIG, _ECHO)
_line_follower = Line_Follower(references=_LINE_FOLLOWER_REFERENCE)
_front_wheel = Front_Wheels()
_back_wheel = Back_Wheels()


def setup():
    pwm = PCA9685.PWM(bus_number=1)
    pwm.setup()
    pwm.frequency = 60
    _distance_sensor.calibrate()


setup()


def measure_distance(*args) -> float:
    """Measure the distance using the ultrasonic sensor and return the distance in cm."""
    return _distance_sensor.measure_distance()


def line_follower_read(*args) -> list[int]:
    """Read the line follower sensor values (5 sensors) and return a list of 0s and 1s."""
    return _line_follower.read_digital()


def set_steering(*args) -> None:
    """Turn the steering wheel to the given angle (45, 135 degrees) based on the input value (-1 to 1)."""
    angleArg: str = args[0]
    angle: int = int((float(angleArg) * 45) + 90)  # from -1, 1 to 45, 135
    _front_wheel.turn(angle)


def set_motor_speed(*args) -> None:
    """Set the motor speed (-100 to 100) based on the input value (-1 to 1)."""
    speedArg: str = args[0]
    # print(f"set_motor_speed: {speedArg}")
    # print(f"set_motor_speed: {float(speedArg)}")
    speed: int = int(float(speedArg) * 100)  # from -1 to 1 to 0 to 100
    _back_wheel.speed = speed

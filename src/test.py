import sys
import time

import RPi.GPIO as GPIO

import utils
import utils.PCF8591
from utils.SunFounder_Line_Follower.Line_Follower import Line_Follower
from utils.SunFounder_PCA9685 import PCA9685, Servo

# import ultrasonic_module

_DEBUG = True
TRIG = 12
ECHO = 16
GPIO.setmode(GPIO.BCM)
LINE_FOLLOWER_REFERENCE = [20, 20, 20, 20, 20]


def setup():
    pwm = PCA9685.PWM(bus_number=1)
    pwm.setup()
    pwm.frequency = 60


def servoInstall():
    servo0 = Servo.Servo(0, bus_number=1)
    servo1 = Servo.Servo(1, bus_number=1)
    servo2 = Servo.Servo(2, bus_number=1)
    servo0.write(90)
    servo1.write(90)
    servo2.write(90)


class UltrasonicSensor:
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


servoInstall()

utils.front_wheels.test()
utils.back_wheels.test()

fw = utils.front_wheels.Front_Wheels()

fw.turn_straight()
input("Wheels are straight.\nPress Enter to continue...")

fw.turn_left()
input("Wheels are left.\nPress Enter to continue...")

fw.turn_right()
input("Wheels are right.\nPress Enter to continue...")

try:
    sensor = UltrasonicSensor(TRIG, ECHO)
    sensor.calibrate()

    lf = Line_Follower(references=LINE_FOLLOWER_REFERENCE)
except KeyboardInterrupt:
    print("Goodbye!")
    sys.exit()


while True:
    try:
        print()
        distance = []
        numOfTry = 25
        med = 0

        for i in range(numOfTry):
            d = sensor.measure_distance()
            distance.append(d)
            time.sleep(sensor.waitTime)
            med += d / numOfTry

        print(f"distance:{med}cm")
        time.sleep(sensor.waitTime)
        # print()
        # print(f"line:{lf.read_analog()}")
        # print(f"line:{lf.read_digital()}")
        time.sleep(0.5)
    except KeyboardInterrupt:
        print("Goodbye!")
        sys.exit()

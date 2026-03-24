import time

import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

TRIG = 12
ECHO = 16
i = 0

GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
print("Calibration.....")
time.sleep(2)

print("Placez un objet......")


try:
    while True:
        GPIO.output(TRIG, True)
        GPIO.output(TRIG, False)

        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()

        pulse_duration = pulse_end - pulse_start

        #       distance = pulse_duration * 17150
        distance = pulse_duration * 16666

        distance = round(distance, 2)

        if distance >= 3:
            i = 1

        print(f"distance:{distance}cm")

        time.sleep(0.05)

except KeyboardInterrupt:
    GPIO.cleanup()

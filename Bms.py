import time
import random
from machine import Pin, ADC, PWM

# Power Management Configurations
BATTERY_VOLTAGE = 12.6  # 3S Li-ion Battery
MAX_CURRENT = 2.5  # A
LOW_BATTERY_THRESHOLD = 20  # Percentage

# Sensor & Module Configurations
LASER_TRANSMITTERS = [Pin(i, Pin.OUT) for i in range(3)]  # 3 Laser Transmitters
LASER_RECEIVERS = [Pin(i + 3, Pin.IN) for i in range(3)]  # 3 Laser Receivers
SENSORS = [ADC(Pin(i + 6)) for i in range(4)]  # 4 Additional Sensors

# BMS Communication
BATTERY_ADC = ADC(Pin(10))  # Battery voltage monitoring

# Alarm System
ALARM = Pin(12, Pin.OUT)

def check_battery():
    battery_level = (BATTERY_ADC.read() / 4095.0) * BATTERY_VOLTAGE
    battery_percentage = (battery_level / BATTERY_VOLTAGE) * 100
    if battery_percentage < LOW_BATTERY_THRESHOLD:
        send_alert("Battery Low: {:.2f}%".format(battery_percentage))
    return battery_percentage

def send_alert(message):
    print("[ALERT]:", message)  # Replace with actual communication to base

def detect_intrusion():
    for receiver in LASER_RECEIVERS:
        if receiver.value() == 0:  # Laser beam interrupted
            trigger_alarm()
            return True
    for sensor in SENSORS:
        if sensor.read() > 2000:  # Threshold detection for sensors
            trigger_alarm()
            return True
    return False

def trigger_alarm():
    print("Intrusion Detected! ALARM TRIGGERED!")
    ALARM.value(1)
    time.sleep(5)
    ALARM.value(0)

while True:
    battery_status = check_battery()
    print("Battery Level: {:.2f}%".format(battery_status))
    if detect_intrusion():
        print("Intrusion Detected")
    time.sleep(1)  # Delay for stability

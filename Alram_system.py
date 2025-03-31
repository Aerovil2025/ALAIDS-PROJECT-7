from machine import Pin, SPI
from time import sleep
from lora import LoRa

lora = LoRa(spi=SPI(1), cs=Pin(18), reset=Pin(14), irq=Pin(26))

buzzer = Pin(15, Pin.OUT)
led_alarm = Pin(2, Pin.OUT)


stumps = {f"x{i}": "active" for i in range(1, 6)}


def trigger_alarm(stump):
        print(f"ALERT from {stump}: Activating Base Camp Alarm!")
    for _ in range(5):
        buzzer.on()
        led_alarm.on()
        sleep(0.5)
        buzzer.off()
        led_alarm.off()
        sleep(0.5)


def destroy_stump(stump):
    """Marks a stump as destroyed"""
    if stump in stumps and stumps[stump] != "destroyed":
        stumps[stump] = "destroyed"
        print(f"Stump {stump} is DESTROYED! Alerting all other stumps...")
        lora.send(f"DESTROY {stump}")
    else:
        print(f"Stump {stump} already destroyed or invalid!")


def manually_turn_off_stump(stump):
    """Manually turns off a stump"""
    if stump in stumps and stumps[stump] == "active":
        stumps[stump] = "off"
        print(f"Stump {stump} turned OFF!")
        lora.send(f"OFF {stump}")
    else:
        print(f"Stump {stump} is already OFF or not active!")


def restore_stump(stump):
    """Restores a stump back to active state"""
    if stump in stumps and stumps[stump] != "active":
        stumps[stump] = "active"
        print(f"Stump {stump} RESTORED to active mode!")
        lora.send(f"RESTORE {stump}")
    else:
        print(f"Stump {stump} is already active or invalid!")


def alarm_off(stump):
    """Turns off the alarm system for a specific stump"""
    print(f"Alarm OFF for {stump}")
    buzzer.off()
    led_alarm.off()
    lora.send(f"ALARM_OFF {stump}")


def check_stump_status():
    """Receives messages and responds accordingly"""
    msg = lora.receive()
    if msg:
        msg = msg.decode("utf-8").strip()
        if "ALERT" in msg:
            stump = msg.split()[-1]
            if stumps.get(stump) == "active":
                trigger_alarm(stump)
        elif msg.startswith("STATUS"):
            lora.send(f"STATUS_REPORT {stumps}")


# Main loop to manage commands
def run_system():
    """Runs the system with real-time user interaction"""
    while True:
        check_stump_status()
        print(f"\nStump Status: {stumps}")

        user_input = input(
            "Enter 'destroy x#', 'off x#', 'restore x#', 'alarm_off x#', or 'exit': ").strip().lower()

        if user_input.startswith("destroy"):
            _, stump = user_input.split()
            destroy_stump(stump)
        elif user_input.startswith("off"):
            _, stump = user_input.split()
            manually_turn_off_stump(stump)
        elif user_input.startswith("restore"):
            _, stump = user_input.split()
            restore_stump(stump)
        elif user_input.startswith("alarm_off"):
            _, stump = user_input.split()
            alarm_off(stump)
        elif user_input == "exit":
            print("System shutting down...")
            break
        else:
            print("Invalid command! Use 'destroy x#', 'off x#', 'restore x#', or 'alarm_off x#' (e.g., 'destroy x3').")


# Run the system
run_system()

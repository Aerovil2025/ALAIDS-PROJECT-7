import serial
import time
import socket
import threading
import itertools

class StumpSensorNetwork:
    def __init__(self, port, baud_rate=115200, stump_count=4, server_ip="192.168.1.100", server_port=5000):
        self.ser = serial.Serial(port, baud_rate, timeout=1)  # ESP32 Serial Connection
        self.stump_count = stump_count
        self.stumps = {f"x{i+1}": True for i in range(stump_count)}  # Stump connection status
        self.sensor_data = {f"x{i+1}": {"Laser": 1, "Photodiode": 1, "PIR": 1, "Radar": 1, "Seismic": 1} for i in range(stump_count)}
        self.alarm_active = False  # Alarm status
        self.stop_alarm = False  # Flag to manually stop the alarm

        # Wi-Fi Setup (STANDBY Mode)
        self.server_ip = server_ip
        self.server_port = server_port
        self.sock = None  # Wi-Fi socket will be initialized only if needed

        # Laser Security System - Dynamic Combinations
        self.x1_transmitters = ["x1t1", "x1t2", "x1t3"]
        self.x2_receivers = ["x2r1", "x2r2", "x2r3"]
        self.all_combinations = list(itertools.permutations(zip(self.x1_transmitters, self.x2_receivers)))
        self.combination_index = 0

    def send_command(self, command):
        """Sends a command to ESP32 and reads response"""
        self.ser.write(command.encode())
        time.sleep(1)
        response = self.ser.readline().decode().strip()
        return response

    def check_stump_status(self):
        """Reads sensor data from ESP32 and checks if any stump connection is broken"""
        for stump in self.stumps:
            response = self.send_command(f"READ {stump}")
            if response:
                laser, photodiode, pir, radar, seismic = map(int, response.split(","))
                self.sensor_data[stump] = {
                    "Laser": laser,
                    "Photodiode": photodiode,
                    "PIR": pir,
                    "Radar": radar,
                    "Seismic": seismic
                }

                # If laser or photodiode is interrupted, check backup sensors
                if laser == 0 or photodiode == 0:
                    print(f"ALERT! Stump {stump} lost laser connection!")
                    if pir == 0 or radar == 0 or seismic == 0:
                        print(f"WARNING! A sensor in stump {stump} is offline! Attempting reactivation...")
                        self.reactivate_sensors(stump)

                    self.trigger_alarm(stump, destroyed=True)
                    self.stumps[stump] = False  # Mark stump as disconnected

                    # Send alert via LoRa
                    if not self.send_lora_message(f"ALERT: {stump} Intrusion detected!"):
                        print("LoRa failed! Switching to Wi-Fi...")
                        self.send_wifi_update()

                    self.reroute_network()

    def reactivate_sensors(self, stump):
        """Attempts to reactivate offline sensors"""
        for sensor in self.sensor_data[stump]:
            if self.sensor_data[stump][sensor] == 0:
                print(f"Reactivating {sensor} on {stump}...")
                response = self.send_command(f"REACTIVATE {stump} {sensor}")
                if response == "OK":
                    self.sensor_data[stump][sensor] = 1
                    print(f"{sensor} on {stump} is now active.")

    def send_lora_message(self, message):
        """Sends an alert message using LoRa"""
        response = self.send_command(f"LORA_SEND {message}")
        if response == "LORA_OK":
            print(f"LoRa Message Sent: {message}")
            return True
        return False

    def connect_wifi(self):
        """Activates Wi-Fi only if LoRa fails"""
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            print(f"Connected to server at {self.server_ip}:{self.server_port} (Wi-Fi Standby Mode Activated)")
        except Exception as e:
            print(f"Wi-Fi Connection Failed: {e}")

    def send_wifi_update(self):
        """Sends network status over Wi-Fi if LoRa fails"""
        if not self.sock:
            self.connect_wifi()  # Connect Wi-Fi only when needed

        try:
            status = str(self.stumps).encode()
            self.sock.send(status)
            print("Wi-Fi Status Sent to Server")
        except Exception as e:
            print(f"Wi-Fi Send Failed: {e}")

    def trigger_alarm(self, stump, destroyed):
        """Triggers alarm for stump failures"""
        if destroyed:
            print(f"ALARM TRIGGERED! Stump {stump} is destroyed! Alarm will sound until manually turned off.")
            self.alarm_active = True
            self.stop_alarm = False
            threading.Thread(target=self.sound_alarm, args=(True,)).start()
        else:
            print(f"ALARM TRIGGERED! Stump {stump} is disabled! Alarm will stop after 25 seconds.")
            threading.Thread(target=self.sound_alarm, args=(False,)).start()

    def sound_alarm(self, indefinite):
        """Simulates alarm sound"""
        start_time = time.time()
        while not self.stop_alarm:
            print("DANGER ALARM SOUNDING!")
            time.sleep(1)
            if not indefinite and time.time() - start_time >= 25:
                break
        print("Alarm stopped.")

    def stop_destroyed_alarm(self):
        """Manually stops the destroyed stump alarm"""
        if self.alarm_active:
            self.stop_alarm = True
            self.alarm_active = False
            print("Destroyed stump alarm has been manually turned off.")

    def reroute_network(self):
        """Re-establishes connectivity if a stump is disabled"""
        active_stumps = [s for s, status in self.stumps.items() if status]
        if len(active_stumps) < 2:
            print("CRITICAL: Network failure! Insufficient active stumps.")
        else:
            print("Rerouting network:", " → ".join(active_stumps))

    def cycle_combinations(self):
        """Cycles through all laser transmitter-receiver combinations every second."""
        while True:
            self.combination_index = (self.combination_index + 1) % len(self.all_combinations)
            combination = self.all_combinations[self.combination_index]
            print("\nActive Laser Connections:")
            for tx, rx in combination:
                print(f"  {tx} → {rx}")
            time.sleep(1)

    def run(self):
        """Continuously monitors the sensor network"""
        threading.Thread(target=self.cycle_combinations, daemon=True).start()  # Start cycling laser combinations

        while True:
            self.check_stump_status()
            self.display_status()
            time.sleep(5)  # Delay before next reading

            user_input = input("Enter 'stop_alarm', 'restore x#', or 'exit': ").strip().lower()
            if user_input == "stop_alarm":
                self.stop_destroyed_alarm()
            elif user_input.startswith("restore"):
                _, stump = user_input.split()
                self.restore_stump(stump)
            elif user_input == "exit":
                print("System shutting down...")
                break
            else:
                print("Invalid command! Use 'stop_alarm', 'restore x#', or 'exit'.")

network = StumpSensorNetwork(port="COM3")
network.run()

import serial
import time
import threading


class StumpSensorNetwork:
    def __init__(self, port, baud_rate=115200, stump_count=4):
        self.ser = serial.Serial(port, baud_rate, timeout=1)  # ESP32 Serial Connection
        self.stump_count = stump_count
        self.stumps = {f"x{i + 1}": True for i in range(stump_count)}  # Stump connection status
        self.sensor_data = {f"x{i + 1}": {"Laser": 1, "Photodiode": 1, "PIR": 1, "Radar": 1, "Seismic": 1} for i in
                            range(stump_count)}
        self.alarm_active = False

    def send_command(self, command):
        """Sends a command to ESP32 and reads response"""
        self.ser.write(command.encode())
        time.sleep(0.5)
        response = self.ser.readline().decode().strip()
        return response

    def classify_intrusion(self, sensor_data):
        """Classifies whether it's a human, animal, or vehicle intrusion"""
        laser = sensor_data["Laser"]
        photodiode = sensor_data["Photodiode"]
        pir = sensor_data["PIR"]
        radar = sensor_data["Radar"]
        seismic = sensor_data["Seismic"]

        if pir == 1 and 0.5 <= radar <= 1.5 and seismic > 3:
            return "Human Detected"
        elif pir == 1 and radar > 1.5 and seismic <= 3:
            return "Animal Detected"
        elif pir == 1 and radar > 3 and seismic > 5:
            return "Vehicle Detected"
        elif pir == 0 and radar == 0 and seismic < 2:
            return "False Alarm (Wind/Insects)"
        else:
            return "Unknown Intrusion"

    def check_stump_status(self):
        """Reads sensor data from ESP32 and classifies movement"""
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
                classification = self.classify_intrusion(self.sensor_data[stump])
                print(f"{stump}: {classification}")

                if classification != "False Alarm (Wind/Insects)":
                    self.trigger_alarm(stump, classification)

    def trigger_alarm(self, stump, classification):
        """Triggers alarm for all intrusions except false alarms"""
        print(f"ALARM TRIGGERED! {classification} detected at {stump}!")
        self.alarm_active = True
        threading.Thread(target=self.sound_alarm).start()

    def sound_alarm(self):
        """Simulates alarm sound"""
        for _ in range(10):
            print("DANGER ALARM SOUNDING!")
            time.sleep(1)
        print("Alarm stopped.")

    def run(self):
        """Continuously monitors the sensor network"""
        while True:
            self.check_stump_status()
            time.sleep(5)


network = StumpSensorNetwork(port="COM3")
network.run()

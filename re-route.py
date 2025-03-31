import time
import threading
import winsound


class StumpNetwork:
    def __init__(self, stump_count):
        self.stumps = {f"x{i + 1}": True for i in range(stump_count)}
        self.route = []  # Dynamic route
        self.stump_coordinates = {f"x{i + 1}": (i * 10, i * 5) for i in range(stump_count)}  # Example coordinates
        self.alarm_active = {}  # Track active alarms for destroyed stumps
        self.alarm_events = {}  # Control stopping of alarms

    def check_connection(self):
        """Dynamically updates the signal route based on available stumps"""
        active_stumps = [stump for stump, status in self.stumps.items() if status]

        if len(active_stumps) < 2:
            print("ALERT! Insufficient stumps to maintain connection!")
            return

        self.route = active_stumps + [active_stumps[0]]  # Ensuring enclosed loop
        print("New route established:", " → ".join(self.route))

    def trigger_alarm(self, stump, continuous=False):
        """Triggers an alarm sound"""
        print(f"ALARM! Stump {stump} at {self.stump_coordinates[stump]} is offline!")
        self.alarm_events[stump] = threading.Event()

        if continuous:
            self.alarm_active[stump] = True
            while not self.alarm_events[stump].is_set():
                winsound.Beep(1000, 5000)
        else:
            for _ in range(25):
                if self.alarm_events[stump].is_set():
                    break
                winsound.Beep(1000, 1000)
                time.sleep(0.2)

    def destroy_stump(self, stump):
        """Simulates a stump being destroyed"""
        if stump in self.stumps and self.stumps[stump]:
            self.stumps[stump] = False
            print(f"ALERT! Stump {stump} at {self.stump_coordinates[stump]} is DESTROYED! Reconfiguring network...")
            self.alarm_active[stump] = True
            threading.Thread(target=self.trigger_alarm, args=(stump, True), daemon=True).start()
            self.check_connection()
        else:
            print(f"Stump {stump} is already offline!")

    def manually_turn_off_stump(self, stump):
        """Simulates a manual shutdown and triggers alarm immediately for 25 seconds"""
        if stump in self.stumps and self.stumps[stump]:
            self.stumps[stump] = False
            print(f"Stump {stump} is manually turned OFF! Adjusting signal route...")
            self.check_connection()
            threading.Thread(target=self.trigger_alarm, args=(stump, False), daemon=True).start()
        else:
            print(f"Stump {stump} is already offline or destroyed!")

    def restore_stump(self, stump):
        """Manually restores a destroyed stump and stops its alarm"""
        if stump in self.stumps and not self.stumps[stump]:
            self.stumps[stump] = True
            if stump in self.alarm_events:
                self.alarm_events[stump].set()  # Stop the alarm immediately
            print(f"Stump {stump} has been manually restored! Reconfiguring network...")
            self.check_connection()
        else:
            print(f"Stump {stump} is already active!")

    def alarm_off(self, stump):
        """Manually stops the alarm for a destroyed stump but does not restore it"""
        if stump in self.alarm_active and self.alarm_active[stump]:
            self.alarm_events[stump].set()  # Stop the alarm
            self.alarm_active[stump] = False
            print(f"Alarm for stump {stump} has been turned off!")
        else:
            print(f"No active alarm for stump {stump}!")

    def display_status(self):
        """Displays current active and inactive stumps"""
        active_stumps = [stump for stump, status in self.stumps.items() if status]
        inactive_stumps = [stump for stump, status in self.stumps.items() if not status]

        print("\nActive Stumps:", ", ".join(active_stumps) if active_stumps else "None")
        print("Offline Stumps:", ", ".join(inactive_stumps) if inactive_stumps else "None")
        print("Current Signal Route:", " → ".join(self.route) if self.route else "No Active Route!")
        print("-" * 40)

    def run_system(self):
        """Runs the system with real-time user interaction"""
        while True:
            self.check_connection()
            self.display_status()

            user_input = input(
                "Enter 'destroy x#', 'off x#', 'restore x#', 'alarm_off x#', or 'exit': ").strip().lower()
            if user_input.startswith("destroy"):
                _, stump = user_input.split()
                self.destroy_stump(stump)
            elif user_input.startswith("off"):
                _, stump = user_input.split()
                self.manually_turn_off_stump(stump)
            elif user_input.startswith("restore"):
                _, stump = user_input.split()
                self.restore_stump(stump)
            elif user_input.startswith("alarm_off"):
                _, stump = user_input.split()
                self.alarm_off(stump)
            elif user_input == "exit":
                print("System shutting down...")
                break
            else:
                print(
                    "Invalid command! Use 'destroy x#', 'off x#', 'restore x#', or 'alarm_off x#' (e.g., 'destroy x3').")


# Get user input for the number of stumps
stump_count = int(input("Enter the number of stumps: "))
network = StumpNetwork(stump_count)
network.run_system()
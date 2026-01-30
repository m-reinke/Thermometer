import tkinter as tk
from AppGUI import Dashboard
from AppSensorsDummy import Sensors
from AppReading import Reading
from AppSensorData import SensorData
import threading
import time

def update_reading_periodically(app, sensorData, sensors, interval=60):
    """
    Function to periodically gather reading every 'interval' seconds and update the app
    """
    def loop():
        while True:
            # Gather the reading (and optionally update the app with it)
            data = sensors.gather_reading()
            data.print()
            sensorData.save(data)
            sensorData.append_data(data)

            app.update_sensor_data(data)  # Assuming update_data method exists in your Dashboard class to handle this

            # Wait for the next interval
            time.sleep(interval)

    # Start the periodic update in a background thread
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

if __name__ == "__main__":
    root = tk.Tk()
    sensorData = SensorData()
    sensors = Sensors()
    app = Dashboard(root, sensorData)

    # Start the periodic gathering of data every 60 seconds
    update_reading_periodically(app, sensorData, sensors, interval=1)

    # Start the Tkinter main loop
    root.mainloop()

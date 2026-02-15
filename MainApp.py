import tkinter as tk
from AppGUI import Dashboard
from AppReading import Reading
from AppSensorData import SensorData
import threading
import time
try:
    print("Trying to import real sensors...")
    from AppSensors import Sensors
except ImportError:
    print("importing dummy sensors...")
    from AppSensorsDummy import Sensors

import logging

logger = logging.getLogger("therm")

def readData(interval):
    try:
        # Gather the reading (and optionally update the app with it)
        data = sensors.gather_reading()
        data.print()
        sensorData.save(data)
        #sensorData.append_data(data)

        app.update_sensor_data(data)  # Assuming update_data method exists in your Dashboard class to handle this       
    except Exception as e:
        logging.error(e, stack_info=True, exc_info=True)
        
def update_reading_periodically(app, sensorData, sensors, interval=60):

    def loop():
        lastExec = time.time() - interval

        while app.running:
            if time.time() - lastExec <= interval:
                time.sleep(1)
                continue;
            lastExec = time.time()
            readData(interval)
        
        # end loop and quit
        logger.info('Shutting down')
        root.quit()
        root.destroy()

    # Start the periodic update in a background thread
    thread = threading.Thread(target=loop, daemon=True)
    thread.start()


if __name__ == "__main__":
    logging.basicConfig(filename='thermometer.log', level=logging.INFO)
    logger.info('Started')


    root = tk.Tk()
    sensorData = SensorData()
    sensors = Sensors()
    app = Dashboard(root, sensorData)

    # sensorData.delete_last24()
    # fakedata = sensors.prior24()
    # sensorData.fake24(fakedata)

    # Start the periodic gathering of data every 60 seconds
    update_reading_periodically(app, sensorData, sensors, interval=15)

    root.after(1000, lambda: root.wm_attributes('-fullscreen', 'true'))

    # Start the Tkinter main loop
    root.mainloop()



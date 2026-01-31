import matplotlib.dates as mdates
from datetime import datetime
import datetime as dt
import sqlite3


from Reading import Reading

#from AppGUI import IAQ_ICONS

# Define the Reading class
class SensorData:
    def __init__(self, dbName="readings.db"):
        self.records = []  # Each record is a dict: {"time": ..., "temp": ..., "humid": ..., "pressure": ..., "iaq": ...}

        self.db_name = dbName
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TEXT,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    gas REAL,
                    iaq REAL,
                    lux REAL
                )
            """)
        
    def save(self, reading):

        """Save the current reading to the database."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if not self.checkDb(cursor):
                return
            # Insert the new reading into the database
            cursor.execute("""
                INSERT INTO readings (time, temperature, humidity, pressure, gas, iaq, lux)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (reading.time, reading.temperature, reading.humidity, reading.pressure, reading.gas, reading.iaq, reading.lux))
            conn.commit()

    def load_data(self):
        conn = sqlite3.connect(self.db_name)
        cursor = conn.cursor()

        if not self.checkDb(cursor):
            conn.close()
            return

        one_day_ago = datetime.now() - dt.timedelta(hours=24)
        query = """
        SELECT time, temperature, humidity, pressure, gas, iaq, lux
        FROM readings
        WHERE time >= ?
        ORDER BY time ASC
        """
        cursor.execute(query, (one_day_ago.isoformat(),))
        rows = cursor.fetchall()

        # Clear previous records
        self.records = []

        for row in rows:
            time_str, temperature, humidity, pressure, gas, iaq, lux = row
            reading = Reading(
                time=datetime.fromisoformat(time_str),
                temperature=temperature,
                humidity=humidity,
                pressure=pressure,
                gas=gas,
                iaq=iaq,
                lux=lux
            )
            self.records.append(reading)

        conn.close()


    def append_data(self, reading):
        """Add a new Reading object to records."""
        if isinstance(reading.time, str):
            reading.time = datetime.fromisoformat(reading.time)
        
        self.records.append(reading)

        # Remove records older than 24 hours
        cutoff = datetime.now() - dt.timedelta(hours=24)
        self.records = [r for r in self.records if r.time >= cutoff]

    # def add_record(self, time, temp, humid, pressure, iaq, gas=0, lux=0):
    #     """Create and add a Reading object."""
    #     reading = Reading(time=time, temperature=temp, humidity=humid,
    #                       pressure=pressure, gas=gas, iaq=iaq, lux=lux)
    #     self.records.append(reading)
    

    # Update has_* methods to work with Reading objects
    def has_temps(self):
        return any(r.temperature is not None for r in self.records)

    def has_humids(self):
        return any(r.humidity is not None for r in self.records)

    def has_pressures(self):
        return any(r.pressure is not None for r in self.records)

    def has_iaqs(self):
        return any(r.iaq is not None for r in self.records)


    def checkDb(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readings';")
        if not cursor.fetchone():
            print("Error: The table 'readings' does not exist.")
            # Do not attempt to close a non-local connection here.
            return False
        return True

    def delete_last24(self):
        """
        Delete all records from the readings table whose 'time' is within the last 24 hours.        
        """
        cutoff_dt = datetime.now() - dt.timedelta(hours=24)
        cutoff_iso = cutoff_dt.isoformat()

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Ensure table exists locally; avoid using checkDb (it may try to close external conn)

            cursor.execute("DELETE FROM readings WHERE time >= ?", (cutoff_iso,))           
            conn.commit()

 
    def fake24(self, readings):
        for reading in readings:
            self.save(reading)


import matplotlib.dates as mdates
from datetime import datetime
import datetime as dt
import sqlite3
import threading
import logging

from AppReading import Reading

logger = logging.getLogger("therm")

# Define the Reading class
class SensorData:
    def __init__(self, dbName="readings.db", save_threshold=1):
        self.records = []
        # Number of save() calls to buffer before computing an averaged reading and writing to DB
        self.save_threshold = 4
        self._save_buffer = []
        self._lock = threading.Lock()

        self.db_name = dbName
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Create table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS readings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    time TIMESTAMP,
                    temperature REAL,
                    humidity REAL,
                    pressure REAL,
                    gas REAL,
                    iaq REAL,
                    lux REAL
                )
            """)
            self.enforce_column(cursor, "temperature_ref", "REAL")
            self.enforce_column(cursor, "humidity_ref", "REAL")

    def enforce_column(self, cursor, column_name, column_type):
        """Ensure a column exists in the readings table; add it if missing."""
        cursor.execute("PRAGMA table_info(readings);")
        columns = [info[1] for info in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE readings ADD COLUMN {column_name} {column_type};")


    def save(self, reading):
        """
        Buffer incoming readings. When buffer length reaches save_threshold,
        compute the average reading and call saveToDb with that averaged reading.
        """
        # Append reading to buffer
        self._save_buffer.append(reading)

        # If buffer hasn't reached the threshold yet, return
        if len(self._save_buffer) < self.save_threshold:
            return

        # Helper to average a numeric attribute, skipping None
        def avg_attr(attr):
            vals = [getattr(r, attr) for r in self._save_buffer if getattr(r, attr) is not None]
            if not vals:
                return None
            return sum(vals) / len(vals)
        def avg_time():
            vals = [ts.time.timestamp() for ts in self._save_buffer]
            if not vals:
                return None
            avg = sum(vals) / len(vals)
            return dt.datetime.fromtimestamp(avg)

        avg_time_value = avg_time()
        avg_temperature = avg_attr("temperature")
        avg_humidity = avg_attr("humidity")
        avg_temperature_ref = avg_attr("temperature_ref")
        avg_humidity_ref = avg_attr("humidity_ref")
        avg_pressure = avg_attr("pressure")
        avg_gas = avg_attr("gas")
        avg_iaq = avg_attr("iaq")
        avg_lux = avg_attr("lux")

        # Create averaged Reading; time stored as ISO string so saveToDb stores it consistently
        averaged = Reading(
            time=avg_time_value,
            temperature=avg_temperature,
            humidity=avg_humidity,
            pressure=avg_pressure,
            gas=avg_gas,
            iaq=avg_iaq,
            lux=avg_lux,
            temperature_ref=avg_temperature_ref,
            humidity_ref=avg_humidity_ref
        )

        # Persist averaged reading
        self.saveToDb(averaged)

        # Optionally append to in-memory records as well
        try:
            self.append_data(averaged)
        except Exception:
            # append_data expects Reading.time to be string or datetime; averaged.time is ISO string, so should be fine.
            pass

        # Clear buffer
        self._save_buffer.clear()


    def saveToDb(self, reading):

        """Save the current reading to the database."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            if not self.checkDb(cursor):
                return
            # Insert the new reading into the database
            cursor.execute("""
                INSERT INTO readings (time, temperature, humidity, pressure, gas, iaq, lux, temperature_ref, humidity_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (reading.time, reading.temperature, reading.humidity, reading.pressure, reading.gas, reading.iaq, reading.lux, reading.temperature_ref, reading.humidity_ref))
            conn.commit()

    def load_data(self):
        with self._lock:
            conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
            cursor = conn.cursor()

            if not self.checkDb(cursor):
                conn.close()
                return

            one_day_ago = datetime.now() - dt.timedelta(hours=24)
            query = """
            SELECT time, temperature, humidity, pressure, gas, iaq, lux, temperature_ref, humidity_ref
            FROM readings
            WHERE time >= ?
            ORDER BY time ASC
            """
            cursor.execute(query, (one_day_ago,))
            rows = cursor.fetchall()

            # Clear previous records
            self.records = []

            for row in rows:
                time, temperature, humidity, pressure, gas, iaq, lux, temperature_ref, humidity_ref = row
                reading = Reading(
                    time=time,
                    temperature=temperature,
                    humidity=humidity,
                    pressure=pressure,
                    gas=gas,
                    iaq=iaq,
                    lux=lux,
                    temperature_ref=temperature_ref,
                    humidity_ref=humidity_ref

                )
                self.records.append(reading)

            conn.close()


    def append_data(self, reading):
        """Add a new Reading object to records."""
        with self._lock:        
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
            logger.error("Error: The table 'readings' does not exist.")
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

    # provide a safe snapshot getter:
    def snapshot(self):
        with self._lock:
            return list(self.records)


import matplotlib.dates as mdates
from datetime import datetime
import datetime as dt
import sqlite3

# Define the Reading class
class SensorData:
    def __init__(self, dbName="readings.db"):
        self.xs = []
        self.temps = []
        self.humids = []
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

        # Check if the 'readings' table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readings';")
        if not self.checkDb(cursor):
            return

        # Query readings from the last 24 hours
        one_day_ago = datetime.now() - dt.timedelta(hours=24)
        query = """
        SELECT time, temperature, humidity
        FROM readings
        WHERE time >= ?
        ORDER BY time ASC
        """
        cursor.execute(query, (one_day_ago,))
        rows = cursor.fetchall()
        # Process results and update data containers
        for row in rows:
            timestamp, temperature, humidity = row
            self.xs.append(mdates.date2num(datetime.fromisoformat(timestamp)))
            self.temps.append(temperature)
            self.humids.append(humidity)
        conn.close()

    def append_data(self, data):
            # Update plot data
        timestamp = mdates.date2num(datetime.now())
        self.xs.append(timestamp)
        self.temps.append(data.temperature)
        self.humids.append(data.humidity)

        # Remove data points older than 24 hours
        one_day_ago = mdates.date2num(datetime.now() - dt.timedelta(hours=24))
        while self.xs and self.xs[0] < one_day_ago:
            self.xs.pop(0)
            self.temps.pop(0)
            self.humids.pop(0)

    def has_humids(self):
        return len(self.humids) > 0
    def has_temps(self):
        return len(self.temps) > 0

    def checkDb(self, cursor):
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='readings';")
        if not cursor.fetchone():
            print("Error: The table 'readings' does not exist.")
            conn.close()
            return False
        return True


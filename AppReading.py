import sqlite3

# Define the Reading class
class Reading:
    def __init__(self, time, temperature, humidity, pressure, gas, iaq, lux):
        self.time = time
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.gas = gas
        self.iaq = iaq
        self.lux = lux

    def save(self, db_name="readings.db"):
        """Save the current reading to the database."""
        with sqlite3.connect(db_name) as conn:
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
            # Insert the new reading into the database
            cursor.execute("""
                INSERT INTO readings (time, temperature, humidity, pressure, gas, iaq, lux)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (self.time, self.temperature, self.humidity, self.pressure, self.gas, self.iaq, self.lux))
            conn.commit()

    def print(self):
        print(self.temperature,self.humidity,self.iaq,self.pressure)

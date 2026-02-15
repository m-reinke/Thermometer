import sqlite3
import logging

logger = logging.getLogger("therm")


# Define the Reading class
class Reading:
    def __init__(self, time, temperature, humidity, pressure, gas, iaq, lux, temperature_ref, humidity_ref):
        self.time = time
        self.temperature = temperature
        self.humidity = humidity
        self.pressure = pressure
        self.gas = gas
        self.iaq = iaq
        self.lux = lux
        self.temperature_ref = temperature_ref
        self.humidity_ref = humidity_ref

    def save(self, db_name="readings.db"):
        """Save the current reading to the database."""
        with sqlite3.connect(db_name) as conn:
            cursor = conn.cursor()
            # Insert the new reading into the database
            cursor.execute("""
                INSERT INTO readings (time, temperature, humidity, pressure, gas, iaq, lux, temperature_ref, humidity_ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (self.time, self.temperature, self.humidity, self.pressure, self.gas, self.iaq, self.lux, self.temperature_ref, self.humidity_ref))
            conn.commit()

    def print(self):
        print(self.temperature,self.humidity,self.iaq,self.pressure)
        logger.info(f"Temp: {self.temperature:.1f}C, Temp_ref: {self.temperature_ref:.1f}C, Humidity: {self.humidity:.0f}%, Humidity_ref: {self.humidity_ref:.0f}%, IAQ: {self.iaq}, Pressure: {self.pressure:.0f} hPa, Gas: {self.gas:.1f}Ohm, Lux: {self.lux:.1f}lx")   
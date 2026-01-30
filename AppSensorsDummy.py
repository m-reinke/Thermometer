from datetime import datetime
from math import isnan
import random
from AppReading import Reading

class Sensors:
    def __init__(self):
        # Initialize the sensors
        self.lastTemp = 20
        self.lasthumidity = 40
        self.lastpressure = 990
        self.lastLux = 200
        self.lastairQuality = 1

        self.deviation = 20

    def getRandom(self, scale):
        rnd = random.randrange(-50, 50) * self.deviation / 10000
        return scale * (1 + rnd)

    # Measure temperature
    def meas_temperature(self):
        self.lastTemp = self.getRandom(self.lastTemp)
        return self.lastTemp

    # Measure humidity
    def meas_humidity(self):
        self.lasthumidity = self.getRandom(self.lasthumidity)
        return self.lasthumidity

    # Measure air pressure
    def meas_pressure(self):
        self.lastpressure = self.getRandom(self.lastpressure)
        return self.lastpressure

    # Measure gas resistance
    def meas_gas(self, n_meas=5):
        self.lastairQuality = self.getRandom(self.lastairQuality)
        return self.lastairQuality

    # Measure brightness
    def meas_lux(self):
        self.lastLux = self.getRandom(self.lastLux)
        return self.lastLux

    # Calculate air quality index
    def calc_iaq(self, h, r):
        if isnan(h) or isnan(r):
            return float('nan')  # Return NaN if inputs are invalid

        # Define humidity contribution
        hum_reference = 40  # Identify optimum
        if h < 38:  # Below optimum, score
            hum_score = 0.25 / hum_reference * h * 100
        elif h <= 42:
            hum_score = 25
        else:
            hum_score = ((-0.25 / (100 - hum_reference) * h) + 0.416666) * 100

        gas_reference = r
        gas_lower_limit = 5000
        gas_upper_limit = 50000
        if gas_reference > gas_upper_limit:
            gas_reference = gas_upper_limit
        elif gas_reference < gas_lower_limit:
            gas_reference = gas_lower_limit

        gas_score = (0.75 / (gas_upper_limit - gas_lower_limit) * gas_reference -
                    (gas_lower_limit * (0.75 / (gas_upper_limit - gas_lower_limit)))) * 100
        return round((100 - hum_score - gas_score) * 5)

    # Gather all sensor readings and create a Reading object
    def gather_reading(self):
        """Gather all sensor readings, create a Reading object, and save it."""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        temperature = self.meas_temperature()
        humidity = self.meas_humidity()
        pressure = self.meas_pressure()
        gas = self.meas_gas()
        lux = self.meas_lux()
        iaq = self.calc_iaq(humidity, gas)
        
        # Create a Reading object
        reading = Reading(current_time, temperature, humidity, pressure, gas, iaq, lux)
        
        return reading



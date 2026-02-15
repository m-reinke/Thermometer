from datetime import datetime
from math import isnan
from AppReading import Reading
from LocalSettings import Localsettings
import board
import busio
import adafruit_bme680
import adafruit_veml7700

import logging
logger = logging.getLogger("therm")
localsettings = Localsettings()

try:
    print("Trying to import HTU31d...")
    import adafruit_htu31d
    has_htu31d = True
except ImportError:
    logger.info("HTU31d not loaded")
    has_htu31d = False


class Sensors:
    def __init__(self):
        # Initialize the sensors
        self.i2c = board.I2C()
        self.bme680 = adafruit_bme680.Adafruit_BME680_I2C(self.i2c)
        self.veml7700 = adafruit_veml7700.VEML7700(self.i2c)
        if has_htu31d:
            self.htu31 = adafruit_htu31d.HTU31D(self.i2c)
        else:
            self.htu31 = None


    # Measure temperature
    def meas_temperature(self):
        return self.safe_measurement(lambda: self.bme680.temperature + localsettings.TEMP_OFFSET)

    # Measure humidity
    def meas_humidity(self):
        return self.safe_measurement(lambda: self.bme680.humidity)

    # Measure air pressure
    def meas_pressure(self):
        return self.safe_measurement(lambda: self.bme680.pressure + localsettings.SEA_LEVEL_CORRECTION)

    # Measure gas resistance
    def meas_gas(self, n_meas=5):
        def gas_avg():
            cumul_ohm = 0
            for _ in range(n_meas):
                cumul_ohm += self.bme680.gas
            return cumul_ohm / n_meas
        return self.safe_measurement(gas_avg)

    # Measure brightness
    def meas_lux(self):
        return self.safe_measurement(lambda: self.veml7700.lux)

    def meas_reference(self):
        if(not self.htu31):
            return float('nan'), float('nan')   
        return self.safe_measurement(lambda: self.htu31.measurements)

    # Define the measurement methods
    def safe_measurement(self, measurement_func):
        """Safely execute a measurement function with NaN as fallback."""
        try:
            return measurement_func()
        except Exception as e:
            print(f"Error in {measurement_func.__name__}: {e}")
            logger = logging.error(e, stack_info=True, exc_info=True)
            return float('nan')  # Return NaN for invalid readings


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
        current_time = datetime.now()
        temperature = self.meas_temperature()
        humidity = self.meas_humidity()
        pressure = self.meas_pressure()
        gas = self.meas_gas()
        lux = self.meas_lux()
        iaq = self.calc_iaq(humidity, gas)
        temperature_ref, humidity_ref = self.meas_reference()
        
        # Create a Reading object
        reading = Reading(current_time, temperature, humidity, pressure, gas, iaq, lux, temperature_ref, humidity_ref)
                
        return reading



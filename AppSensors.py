from datetime import datetime
from math import isnan
import board
import adafruit_bme680
import adafruit_veml7700

class Sensors:
    def __init__():
        # Initialize the sensors
        self.i2c = board.I2C()
        self.bme680 = adafruit_bme680.Adafruit_BME680_I2C(i2c)
        self.veml7700 = adafruit_veml7700.VEML7700(i2c)

        self.TEMP_OFFSET = -5.3  # Calibrate temperature sensor

    # Measure temperature
    def meas_temperature():
        return self.safe_measurement(lambda: self.bme680.temperature + self.TEMP_OFFSET)

    # Measure humidity
    def meas_humidity():
        return self.safe_measurement(lambda: self.bme680.humidity)

    # Measure air pressure
    def meas_pressure():
        return self.safe_measurement(lambda: self.bme680.pressure)

    # Measure gas resistance
    def meas_gas(n_meas=5):
        def gas_avg():
            cumul_ohm = 0
            for _ in range(n_meas):
                cumul_ohm += self.bme680.gas
            return cumul_ohm / n_meas
        return safe_measurement(gas_avg)

    # Measure brightness
    def meas_lux():
        return safe_measurement(lambda: self.veml7700.lux)

    # Define the measurement methods
    def safe_measurement(measurement_func):
        """Safely execute a measurement function with NaN as fallback."""
        try:
            return measurement_func()
        except Exception as e:
            print(f"Error in {measurement_func.__name__}: {e}")
            return float('nan')  # Return NaN for invalid readings


    # Calculate air quality index
    def calc_iaq(h, r):
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



class Localsettings:
    def __init__(self):
        self.TEMP_OFFSET = -0.2  # Calibrate temperature sensor
        self.SEA_LEVEL_CORRECTION = 0  # hPa correction for sea level pressure in Chicago

        self.LIGTH_INACTIVE_THRESHOLD = 10  # Lux threshold for inactive light conditions
        self.LIGTH_LOW_THRESHOLD = 10  # Lux threshold for inactive light conditions
        self.LIGTH_HIGH_THRESHOLD = 10  # Lux threshold for inactive light conditions

        self.SCREEN_LOW_LEVEL  = 50 # backlight level for low screen brightness

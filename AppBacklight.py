from LocalSettings import Localsettings
from rpi_backlight import Backlight
import logging

backlight = Backlight()
logger = logging.getLogger("therm")
localsettings = Localsettings()

class AppBacklight:
    def __init__(self):
        self.currentBrightness = 0
    
    def set_brightness(self, lux):
        brightness = self.getBacklightLevel(lux)
        if brightness == self.currentBrightness:
            return;

        print(f"Backlight brightness set to {self.brightness}%")
        backlight.brightness = brightness
        self.currentBrightness = brightness

    def get_brightness(self):
        return self.currentBrightness  

    def getBacklightLevel(lux):
        if lux < localsettings.LIGTH_INACTIVE_THRESHOLD:
            return 0
        elif lux < localsettings.LIGTH_LOW_THRESHOLD:
            return localsettings.SCREEN_LOW_LEVEL
        elif lux > localsettings.LIGTH_HIGH_THRESHOLD:
            return 100
        else:
            return (100 - localsettings.SCREEN_LOW_LEVEL) * (lux - localsettings.LIGTH_LOW_THRESHOLD) / (localsettings.LIGTH_HIGH_THRESHOLD - localsettings.LIGTH_LOW_THRESHOLD) + localsettings.SCREEN_LOW_LEVEL
from re import I
import numpy as np
import tkinter as tk
import tkinter.font as tkFont
import tkinter.messagebox as mb

from datetime import datetime, timedelta

import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import animation, style
from matplotlib.figure import Figure
import matplotlib.dates as mdates

from PIL import ImageTk, Image
from AppSensorData import SensorData
from AppReading import Reading
import logging

logger = logging.getLogger("therm")


# ────────────────────────
# Configuration Constants
# ────────────────────────
UPDATE_INTERVAL_MS = 1000
PLOT_WINDOW = timedelta(hours=24)

PRESSURE_ICONS = [
    (973.5, "stormcloudcloud.png"),
    (990.5, "raincloud.png"),
    (1007.5, "cloud.png"),
    (1024.4, "intermediate.png"),
    (float("inf"), "sun.png"),
]

IAQ_ICONS = [
    (50, "green.png"),
    (100, "yellow.png"),
    (150, "orange.png"),
    (200, "red.png"),
    (300, "purple.png"),
    (float("inf"), "maroon.png"),
]

matplotlib.use("TkAgg")
style.use("dark_background")


class Dashboard:
    def __init__(self, root: tk.Tk, sensor_data: SensorData):
        self.root = root
        self.sensor_data = sensor_data

        self.root.configure(bg="black")

        # Plot visibility
        self.second_axes = "humid"

        # Load stored data
        self.sensor_data.load_data()
        self.datacount = len(self.sensor_data.records)

        # Cache images
        self._load_icons()

        self._setup_ui()
        self._bind_events()
        self._setup_plot()

        # Start animation
        self.ani = animation.FuncAnimation(
            self.fig, self.animate, interval=UPDATE_INTERVAL_MS
        )

        self.running = True

        self.update_time_and_date()

    def exit_gui(self):
        if mb.askyesno("Exit", "Are you sure you want to exit?"):
            self.running = False

    # ────────────────────────
    # UI Setup
    # ────────────────────────
    def _setup_ui(self):
        self.root.title("Dashboard")
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid: 4 rows, 4 columns
        for i in range(4):
            self.frame.grid_rowconfigure(i, weight=1)
        for i in range(4):
            self.frame.grid_columnconfigure(i, weight=1)

        # ── PLOT (top left, 2/3 width)
        self.plot_frame = tk.Frame(self.frame, bg="black")
        self.plot_frame.grid(row=0, column=1, rowspan=3, columnspan=3, sticky="nsew")

        # ── TIME (top right, 1/3 width)
        self.time_label = tk.Label(
            self.frame, bg="black", fg="white", font=("Helvetica", 96)
        )
        self.time_label.grid(row=1, column=0, rowspan=1, sticky="new", padx = (0,10), ipadx =15)


        # ── DATE (above bottom row)
        self.date_label = tk.Label(
            self.frame, bg="black", fg="white", font=("Helvetica", 36)
        )
        self.date_label.grid(row=0, column=0, columnspan=1, sticky="n")
        self.date_label.bind("<Button-1>", lambda e: self.exit_gui())

        # ── HUMIDITY AND TEMPERATURE (bottom left)
        self.label_humid = tk.Label(
            self.frame, text="Humidity: --%", bg="black", fg="white", font=("Helvetica", 24)
        )
        self.label_humid.grid(row=3, column=1, sticky="w", padx=10)
        self.label_humid.bind("<Button-1>", lambda e: self.toggle_axes("humid"))

        self.label_temp = tk.Label(
            self.frame, text="--°C", bg="black", fg="white", font=("Helvetica", 40)
        )
        self.label_temp.grid(row=2, column=0, sticky="new", padx=10)

        # ── PRESSURE ICON (bottom left)
        self.weather_img_label = tk.Label(self.frame, bg="black")
        self.weather_img_label.grid(row=3, column=0, sticky="nsew", padx=10)
        self.weather_img_label.bind("<Button-1>", lambda e: self.toggle_axes("pressure"))

        # ── IAQ (bottom right)
        self.label_iaq = tk.Label(
            self.frame, text="IAQ: ", bg="black", fg="white", font=("Helvetica", 24)
        )
        self.label_iaq.grid(row=3, column=2, sticky="e", padx=10)

        self.iaq_img_label = tk.Label(self.frame, bg="black")
        self.iaq_img_label.grid(row=3, column=3, sticky="w", padx=10)
        self.iaq_img_label.bind("<Button-1>", lambda e: self.toggle_axes("iaq"))


        

    # ────────────────────────
    # Plot Setup
    # ────────────────────────
    def _setup_plot(self):
        self.fig = Figure()
        self.ax_temp = self.fig.add_subplot(111)
        self.ax_second = self.ax_temp.twinx()

        self.second_fill = self.ax_second.fill_between([], [], alpha=0.3, color="tab:red")
        (self.temp_line,) = self.ax_temp.plot([], [], color="tab:blue", linewidth=2)

        #self.ax_secondary.set_ylabel("Humidity (%)", color="tab:red")
        self.ax_temp.set_ylabel("Temperature (°C)", color="tab:blue")

        self.ax_second.set_ylabel("")
        
        self.ax_temp.xaxis.set_major_locator(mdates.HourLocator(interval=3))
        self.ax_temp.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        self.fig.autofmt_xdate()
        self.fig.tight_layout(pad=2)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


    # ────────────────────────
    # Event Handling
    # ────────────────────────
    def _bind_events(self):
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def end_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)

    def toggle_plot(self, key):
        self.plot_visible[key] = not self.plot_visible[key]

    def toggle_axes(self, mode):
        # Toggle off if already active
        if self.second_axes == mode:
            self.second_axes = None
        else:
            self.second_axes = mode

    # ────────────────────────
    # Time / Sensor Updates
    # ────────────────────────
    def update_time_and_date(self):
        now = datetime.now()
        self.time_label.config(text=now.strftime("%H:%M"))
        self.date_label.config(text=now.strftime("%b %d, %Y"))
        self.root.after(UPDATE_INTERVAL_MS, self.update_time_and_date)

    def update_sensor_data(self, reading: Reading):
        """Update labels and icons from a Reading object."""
        self.label_temp.config(text=f"{reading.temperature:.1f}°C")
        self.label_humid.config(text=f"Humidity: {reading.humidity:.0f}% {self.datacount:.0f}")

        self.weather_img_label.config(image=self._select_icon(reading.pressure, self.weather_icons))
        self.iaq_img_label.config(image=self._select_icon(reading.iaq, self.iaq_icons))
    # ────────────────────────
    # Animation Loop
    # ────────────────────────
    def animate(self, _):
        with self.sensor_data._lock:
            self.datacount = len(self.sensor_data.records)

            times = [mdates.date2num(r.time) for r in self.sensor_data.records]

            if not times:
                return

            # ── Apply 24h window
            end = max(times)
            start = mdates.date2num(
                mdates.num2date(end) - PLOT_WINDOW
            )

            self.ax_temp.set_xlim(start, end)
            self.ax_second.set_xlim(start, end)

            if self.sensor_data.has_temps():
                temps = [r.temperature for r in self.sensor_data.records]
                self.temp_line.set_data(times, temps)

                tmin, tmax = min(temps), max(temps)
                self.ax_temp.set_ylim(tmin - 1, tmax + 1)

            # Clear old fills
            for artist in list(self.ax_second.collections):
                artist.remove()

            # Secondary axis
            data = None

            if self.second_axes == "humid" and self.sensor_data.has_humids():
                data = [r.humidity for r in self.sensor_data.records]
                label, color, ymin, ymax = "Humidity (%)", "tab:red", 0, 100

            elif self.second_axes == "iaq" and self.sensor_data.has_iaqs():
                data = [r.iaq for r in self.sensor_data.records]
                label, color = "IAQ", "tab:green"
                ymin, ymax = min(data) - 5, max(data) + 5

            elif self.second_axes == "pressure" and self.sensor_data.has_pressures():
                data = [r.pressure for r in self.sensor_data.records]
                label, color = "Pressure (hPa)", "tab:purple"
                ymin, ymax = min(data) - 2, max(data) + 2

            if data is not None:
                self.ax_second.fill_between(times, data, color=color, alpha=0.3)
                self.ax_second.set_ylabel(label, color=color)
                self.ax_second.set_ylim(ymin, ymax)
            else:
                self.ax_second.set_ylabel("")

            self.canvas.draw_idle()

        

    # ────────────────────────
    # Icon Utilities
    # ────────────────────────
    def _load_icons(self):
        self.weather_icons = self._cache_icons(PRESSURE_ICONS)
        self.iaq_icons = self._cache_icons(IAQ_ICONS)

    def _cache_icons(self, icon_map):
        return [(limit, ImageTk.PhotoImage(Image.open(path))) for limit, path in icon_map]

    @staticmethod
    def _select_icon(value, icon_map):
        for limit, icon in icon_map:
            if value <= limit:
                return icon

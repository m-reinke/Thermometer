import numpy as np
import threading
import tkinter as tk
import tkinter.font as tkFont
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib import animation
from matplotlib import style
from matplotlib.figure import Figure
from datetime import datetime, timedelta
import datetime as dt
from PIL import ImageTk, Image
import matplotlib.dates as mdates
from AppSensorData import SensorData


matplotlib.use('TkAgg')
style.use("dark_background")


class Dashboard:
    def __init__(self, root, sensorData):
        self.root = root
        self.sensor_data = sensorData
        #self.root.attributes("-fullscreen", True)  # Default to fullscreen
        self.root.configure(bg='black')

        # Data containers
        self.max_elements = 50

        # Plot visibility flags
        self.humid_plot_visible = True
        self.temp_plot_visible = True

        # Load historical data
        self.sensor_data.load_data()

        self.setup_ui()
        self.bind_events()

        # Animation setup
        self.ani = animation.FuncAnimation(self.fig, self.animate, interval=1000)  # Update every second

        # Trigger updates
        self.update_time_and_date()  # Start time/date updates on initialization
    
    def setup_ui(self):
        self.root.title("Dashboard")
        self.frame = tk.Frame(self.root, bg="black")
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.dfont = tkFont.Font(size=-6)

        # Grid layout
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_rowconfigure(3, weight=1)
        self.frame.grid_rowconfigure(4, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_columnconfigure(1, weight=1)
        self.frame.grid_columnconfigure(2, weight=1)
        self.frame.grid_columnconfigure(3, weight=1)
        self.frame.grid_columnconfigure(4, weight=1)
        self.frame.grid_columnconfigure(5, weight=1)

        # Date Label (at the top, across the first three columns)
        self.date_label = tk.Label(self.frame, text="", bg="black", fg="white", font=("Helvetica", 36))
        self.date_label.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=10, pady=(20, 10))

        # Time Label (aligned with plot on the same y-height)
        self.time_label = tk.Label(self.frame, text="", bg="black", fg="white", font=("Helvetica", 96))
        self.time_label.grid(row=1, column=0, columnspan=3, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Temperature Label and Weather Image (in the second row, right side)
        self.label_temp = tk.Label(self.frame, text="--°C", bg="black", fg="white", font=("Helvetica", 36))
        self.label_temp.grid(row=0, column=3, columnspan=2, padx=10)

        self.weather_img_label = tk.Label(self.frame, bg="black")
        self.weather_img_label.grid(row=0, column=5, padx=5)

        # Plot (size 2x2, aligned to the right, adjust space for y-axes)
        self.plot_frame = tk.Frame(self.frame, bg="black")
        self.plot_frame.grid(row=1, column=3, rowspan=2, columnspan=3, sticky="nse", padx=10, pady=10)
        self.fig = Figure(figsize=(3.5, 2))  # Increased size for the plot
        self.ax1 = self.fig.add_subplot(1, 1, 1)
        self.ax2 = self.ax1.twinx()
        
        # Ensure proper layout of axes and labels
        self.fig.tight_layout(pad=2.0)  # Adjusts spacing between plot and labels

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_frame)
        self.canvas_plot = self.canvas.get_tk_widget()
        self.canvas_plot.grid(row=0, column=0, sticky="nse")

        # IAQ Image Below Plot (aligned below the plot, in row 3)
        self.label_iaq = tk.Label(self.frame, text="Air Quality:", bg="black", fg="white", font=("Helvetica", 24))
        self.label_iaq.grid(row=3, column=4, sticky="se", padx=10, pady=(10, 5))

        self.iaq_img_label = tk.Label(self.frame, bg="black")
        self.iaq_img_label.grid(row=3, column=5, rowspan=2,sticky="s", padx=10, pady=(5, 20))

        # Humidity Label (left side of the plot, align with Air Quality)
        self.label_humid = tk.Label(self.frame, text="Humidity: --%", bg="black", fg="white", font=("Helvetica", 24))
        self.label_humid.grid(row=3, column=0, columnspan=3, sticky="sew", padx=10, pady=10)

        # Bottom Right: Buttons for toggling visibility
        self.button_frame = tk.Frame(self.frame, bg="black")
        self.button_frame.grid(row=4, column=3, columnspan=2, sticky="e", padx=10, pady=10)
        self.btn_toggle_temp = tk.Button(
            self.button_frame, text="Temperature Plot", command=self.toggle_temp_visibility, bg="gray", fg="white"
        )
        self.btn_toggle_humid = tk.Button(
            self.button_frame, text="Humidity Plot", command=self.toggle_humid_visibility, bg="gray", fg="white"
        )
        self.btn_toggle_temp.grid(row=0, column=0, padx=5)
        self.btn_toggle_humid.grid(row=0, column=1, padx=5)

    def bind_events(self):
        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.end_fullscreen)

    def toggle_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    def end_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)

    def toggle_temp_visibility(self):
        self.temp_plot_visible = not self.temp_plot_visible

    def toggle_humid_visibility(self):
        self.humid_plot_visible = not self.humid_plot_visible

    def update_time_and_date(self):
        """Updates the time and date labels every second."""
        current_time = datetime.now().strftime("%H:%M")
        current_date = datetime.now().strftime("%b %d, %Y")
        self.time_label.configure(text=current_time)
        self.date_label.configure(text=current_date)

        # Schedule next update in 1 second
        self.root.after(1000, self.update_time_and_date)
    
    def update_sensor_data(self, data):
        """Updates the sensor data using the provided data."""
        if data is None:
            print("Error: Received None data in update_sensor_data.")
            return

        self.label_temp.configure(text=f"{data.temperature:.1f}°C")
        self.label_humid.configure(text=f"Humidity: {data.humidity:.0f}%")

        # Update weather and IAQ images
        weather_image = weatherimg(data.pressure)
        iaq_image = iaqimg(data.iaq)
        self.weather_img_label.configure(image=weather_image)
        self.weather_img_label.image = weather_image
        self.iaq_img_label.configure(image=iaq_image)
        self.iaq_img_label.image = iaq_image

        # Trigger the plot update
        #self.animate(None)  # Call animate to refresh the plot

    def animate(self, i):
        """Updates the plot with the latest data."""
        # Plot updates for temperature and humidity
        self.ax1.clear()
        self.ax2.clear()        

        if self.humid_plot_visible and self.sensor_data.has_humids():
            color = 'tab:red'
            self.ax1.fill_between(self.sensor_data.xs, self.sensor_data.humids, 0, linewidth=2, color=color, alpha=0.3)
            self.ax1.set_ylabel('Humidity (%)', color=color)
            self.ax1.tick_params(axis='y', labelcolor=color)
            self.ax1.set_ylim([np.floor(min(self.sensor_data.humids) / 5) * 5, np.ceil(max(self.sensor_data.humids) / 5) * 5])

        if self.temp_plot_visible and self.sensor_data.has_temps():
            color = 'tab:blue'
            self.ax2.plot(self.sensor_data.xs, self.sensor_data.temps, linewidth=2, color=color)
            self.ax2.set_ylabel('Temperature (°C)', color=color)
            self.ax2.tick_params(axis='y', labelcolor=color)
            self.ax2.set_ylim([np.floor(min(self.sensor_data.temps)), np.ceil(max(self.sensor_data.temps))])

        # Set the x-axis limit to the last 24 hours
        one_day_ago = mdates.date2num(datetime.now() - dt.timedelta(minutes=1))
        self.ax1.set_xlim([one_day_ago, mdates.date2num(datetime.now())])

        # Format the x-axis labels as hours and minutes
        self.ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        self.fig.autofmt_xdate()

        self.canvas.draw()

# Functions for images
def weatherimg(press):
    if press <= 973.5:
        return ImageTk.PhotoImage(Image.open("stormcloudcloud.png"))
    elif press <= 990.5:
        return ImageTk.PhotoImage(Image.open("raincloud.png"))
    elif press <= 1007.5:
        return ImageTk.PhotoImage(Image.open("cloud.png"))
    elif press <= 1024.4:
        return ImageTk.PhotoImage(Image.open("intermediate.png"))
    else:
        return ImageTk.PhotoImage(Image.open("sun.png"))


def iaqimg(iaq):
    if iaq <= 50:
        return ImageTk.PhotoImage(Image.open("green.png"))
    elif iaq <= 100:
        return ImageTk.PhotoImage(Image.open("yellow.png"))
    elif iaq <= 150:
        return ImageTk.PhotoImage(Image.open("orange.png"))
    elif iaq <= 200:
        return ImageTk.PhotoImage(Image.open("red.png"))
    elif iaq <= 300:
        return ImageTk.PhotoImage(Image.open("purple.png"))
    else:
        return ImageTk.PhotoImage(Image.open("maroon.png"))

from PyQt6.QtWidgets import QWidget, QVBoxLayout
import pyqtgraph as pg

class DataTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.main_window = parent
        self.num_values = 6  # Assuming 6 values from the IMU
        self.curves = []  # Store multiple lines for each value
        self.data_buffers = [[] for _ in range(self.num_values)]  # Moving window for each value
        self.max_points = 200  # ~20 seconds of data if sampling every 100ms
        self.sensor_labels = ["Sensor 1", "Sensor 2", "Sensor 3", "Sensor 4", "Sensor 5", "Sensor 6"] # Labels for the legend
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.graph = pg.PlotWidget(title="Orientation Sensor Measurements Over Time Steps")
        self.graph.setLabel('left', "Angular Deviation")
        self.graph.setLabel('bottom', "Step")
        layout.addWidget(self.graph)

        colors = ['r', 'g', 'b', 'c', 'm', 'y']  # Different colors for each line
        for i in range(self.num_values):
            curve = self.graph.plot(pen=colors[i % len(colors)], name=self.sensor_labels[i])
            self.curves.append(curve)

        self.graph.addLegend()
        self.setLayout(layout)

    def update_plot(self, new_values):
        if len(new_values) == self.num_values:
            for i in range(self.num_values):
                self.data_buffers[i].append(new_values[i])
                if len(self.data_buffers[i]) > self.max_points:
                    self.data_buffers[i].pop(0)
                self.curves[i].setData(self.data_buffers[i])
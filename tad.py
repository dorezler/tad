import pandas as pd
import requests
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class ChartsCanvas(FigureCanvasQTAgg):
    def __init__(self):
        self.figure = Figure(figsize=(10, 4), tight_layout=True)
        super().__init__(self.figure)


class TemperatureAnalysisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.original_df = pd.DataFrame()
        self.df = pd.DataFrame()
        self.sensor_checkboxes = {}
        self.setCentralWidget(main_widget)
        self.setWindowTitle("TAD - Temperature Analysis Dashboard")
        self.statusBar().showMessage("Please load data to get started.")

        # Level 1 widget: title banner
        banner_widget = QSvgWidget("tad_banner.svg")
        banner_widget.setFixedHeight(100)
        main_layout.addWidget(banner_widget)

        # Level 1 widget: load/save section
        load_save_widget = QWidget()
        load_save_layout = QHBoxLayout(load_save_widget)
        # Level 2 widget: load frame
        load_frame_widget = QGroupBox("Load data")
        load_layout = QHBoxLayout(load_frame_widget)
        load_from_disk_button = QPushButton("From disk")
        load_from_disk_button.clicked.connect(self.open_file)
        load_layout.addWidget(load_from_disk_button)
        load_from_network_button = QPushButton("From network")
        load_from_network_button.clicked.connect(self.open_network_file)
        load_layout.addWidget(load_from_network_button)
        load_layout.addWidget(QLabel("Supported formats: CSV, JSON"))
        load_layout.addStretch()
        load_save_layout.addWidget(load_frame_widget)
        # Level 2 widget: save frame
        save_frame_widget = QGroupBox("Save data")
        save_layout = QHBoxLayout(save_frame_widget)
        save_as_button = QPushButton("Save as")
        save_as_button.clicked.connect(self.save_file)
        save_layout.addWidget(save_as_button)
        save_layout.addWidget(QLabel("Supported formats: CSV, JSON, PDF report"))
        save_layout.addStretch()
        load_save_layout.addWidget(save_frame_widget)
        main_layout.addWidget(load_save_widget)

        # Level 1 widget: filters frame
        filters_frame_widget = QGroupBox("Filters")
        filters_layout = QVBoxLayout(filters_frame_widget)
        # Level 2 widget: sensor selection with checkboxes
        sensors_widget = QWidget()
        sensors_layout = QHBoxLayout(sensors_widget)
        sensors_layout.addWidget(QLabel("Sensors:"))
        self.sensors_values_widget = QWidget()
        self.sensors_values_layout = QHBoxLayout(self.sensors_values_widget)
        self.sensors_values_layout.setContentsMargins(0, 0, 0, 0)
        self.sensors_values_layout.setSpacing(8)
        sensors_layout.addWidget(self.sensors_values_widget)
        sensors_layout.addStretch()
        filters_layout.addWidget(sensors_widget)
        # Level 2 widget: temperature range selection with a slider
        temperature_widget = QWidget()
        temperature_layout = QHBoxLayout(temperature_widget)
        temperature_layout.addWidget(QLabel("Temperature:"))
        filters_layout.addWidget(temperature_widget)
        main_layout.addWidget(filters_frame_widget)

        # Level 1 widget: results section with tabs
        results_tabs_widget = QTabWidget()
        # Level 2 widget: data table tab
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.table_label = QLabel("Please load data to get started.")
        self.table_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.table_label)
        self.data_table = QTableWidget()
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.setVisible(False)
        table_layout.addWidget(self.data_table)
        results_tabs_widget.addTab(table_widget, "Data")
        # Level 2 widget: statistics tab
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        self.stats_label = QLabel("Please load data to get started.")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(self.stats_label)
        self.stats_frames_container = QWidget()
        self.stats_frames_layout = QGridLayout(self.stats_frames_container)
        self.stats_frames_layout.setContentsMargins(16, 0, 16, 0)
        self.stats_frames_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.stats_frames_layout.setHorizontalSpacing(16)
        self.stats_frames_layout.setVerticalSpacing(16)
        for column_index in range(4):
            self.stats_frames_layout.setColumnStretch(column_index, 1)
        self.stats_scroll_area = QScrollArea()
        self.stats_scroll_area.setWidgetResizable(True)
        self.stats_scroll_area.setWidget(self.stats_frames_container)
        self.stats_scroll_area.setVisible(False)
        stats_layout.addWidget(self.stats_scroll_area)
        results_tabs_widget.addTab(stats_widget, "Statistics")
        # Level 2 widget: visualizations tab
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        self.charts_label = QLabel("Please load data to get started.")
        self.charts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self.charts_label)
        self.charts_canvas = ChartsCanvas()
        self.charts_canvas.setVisible(False)
        charts_layout.addWidget(self.charts_canvas)
        results_tabs_widget.addTab(charts_widget, "Visualizations")
        main_layout.addWidget(results_tabs_widget)

    def load_csv(self, csv_file_path):
        self.original_df = pd.read_csv(csv_file_path)
        self.process_loaded_data(csv_file_path)

    def load_json(self, json_file_path):
        self.original_df = pd.read_json(json_file_path, orient="records")
        self.process_loaded_data(json_file_path)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open data file",
            "",
            "CSV files (*.csv);;JSON files (*.json)",
        )
        if file_path.lower().endswith(".csv"):
            self.load_csv(file_path)
        elif file_path.lower().endswith(".json"):
            self.load_json(file_path)

    def open_network_file(self):
        url, ok = QInputDialog.getText(self, "Load data from network", "Data URL:")
        if not ok or not url.strip():
            return
        url = url.strip()
        try:
            response = requests.get(url, timeout=10)
            self.original_df = pd.DataFrame.from_records(response.json())
        except Exception:
            self.original_df = pd.read_csv(url)
        self.process_loaded_data(url)

    def process_loaded_data(self, data_source):
        self.original_df = self.original_df[["timestamp", "sensor_id", "temperature"]]
        self.original_df["timestamp"] = pd.to_datetime(self.original_df["timestamp"])
        self.refresh_sensor_filters()
        self.apply_filters()
        self.statusBar().showMessage(f"Loaded {data_source} ({len(self.original_df)} rows).")

    def refresh_sensor_filters(self):
        while self.sensors_values_layout.count():
            item = self.sensors_values_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self.sensor_checkboxes = {}
        if self.original_df.empty:
            return
        for sensor_id in sorted(self.original_df["sensor_id"].dropna().unique()):
            checkbox = QCheckBox(str(sensor_id))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.apply_filters)
            self.sensors_values_layout.addWidget(checkbox)
            self.sensor_checkboxes[sensor_id] = checkbox

    def apply_filters(self):
        if self.original_df.empty:
            self.df = self.original_df.copy()
        else:
            selected_sensors = [
                sensor_id for sensor_id, checkbox in self.sensor_checkboxes.items() if checkbox.isChecked()
            ]
            if selected_sensors:
                self.df = self.original_df[self.original_df["sensor_id"].isin(selected_sensors)].copy()
            else:
                self.df = self.original_df.iloc[0:0].copy()
        self.update_data_table()
        self.update_statistics_label()
        self.update_visualizations()

    def save_file(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save data file", "", "CSV files (*.csv);;JSON files (*.json)"
        )
        if not file_path:
            return
        if selected_filter.startswith("JSON") or file_path.lower().endswith(".json"):
            if not file_path.lower().endswith(".json"):
                file_path = f"{file_path}.json"
            self.df.to_json(file_path, date_format="iso", indent=2, orient="records")
        else:
            if not file_path.lower().endswith(".csv"):
                file_path = f"{file_path}.csv"
            self.df.to_csv(file_path, index=False)
        self.statusBar().showMessage(f"Saved data to {file_path} ({len(self.df)} rows).")

    def update_data_table(self):
        if self.df.empty:
            self.table_label.setVisible(True)
            self.table_label.setText("No data for current filters.")
            self.data_table.setVisible(False)
            return
        self.table_label.setVisible(False)
        self.data_table.setVisible(True)
        self.data_table.setRowCount(len(self.df))
        self.data_table.setColumnCount(len(self.df.columns))
        self.data_table.setHorizontalHeaderLabels([str(column) for column in self.df.columns])
        for row_index, (_, row) in enumerate(self.df.iterrows()):
            for column_index, value in enumerate(row):
                self.data_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def update_statistics_label(self):
        if self.df.empty:
            self.stats_label.setVisible(True)
            if self.original_df.empty:
                self.stats_label.setText("Please load data to get started.")
            else:
                self.stats_label.setText("No data for current filters.")
            self.stats_scroll_area.setVisible(False)
            while self.stats_frames_layout.count():
                item = self.stats_frames_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            return
        self.stats_label.setVisible(False)
        self.stats_scroll_area.setVisible(True)
        while self.stats_frames_layout.count():
            item = self.stats_frames_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        global_stats_box = QGroupBox("Global statistics (all sensors)")
        global_stats_layout = QVBoxLayout(global_stats_box)
        global_stats_label = QLabel(
            self.df["temperature"].describe().to_string(float_format=lambda value: f"{value:.1f}")
        )
        global_stats_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        global_stats_layout.addWidget(global_stats_label)
        self.stats_frames_layout.addWidget(global_stats_box, 0, 0, 1, 4)

        for index, (sensor_id, sensor_data) in enumerate(self.df.groupby("sensor_id")):
            sensor_stats_box = QGroupBox(f"Sensor {sensor_id}")
            sensor_stats_layout = QVBoxLayout(sensor_stats_box)
            sensor_stats_text = (
                sensor_data["temperature"].describe().to_string(float_format=lambda value: f"{value:.1f}")
            )
            sensor_stats_label = QLabel(sensor_stats_text)
            sensor_stats_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            sensor_stats_layout.addWidget(sensor_stats_label)
            row_index = (index // 4) + 1
            column_index = index % 4
            self.stats_frames_layout.addWidget(sensor_stats_box, row_index, column_index)

    def update_visualizations(self):
        if self.df.empty:
            self.charts_label.setVisible(True)
            if self.original_df.empty:
                self.charts_label.setText("Please load data to get started.")
            else:
                self.charts_label.setText("No data for current filters.")
            self.charts_canvas.setVisible(False)
            return
        self.charts_label.setVisible(False)
        self.charts_canvas.setVisible(True)
        figure = self.charts_canvas.figure
        figure.clear()
        line_chart_axis = figure.add_subplot(1, 2, 1)
        histogram_axis = figure.add_subplot(1, 2, 2)
        line_chart_data = self.df.sort_values("timestamp")
        line_color_map = colormaps["tab10"]
        sensors_count = line_chart_data["sensor_id"].nunique()
        for index, (sensor_id, sensor_data) in enumerate(line_chart_data.groupby("sensor_id")):
            color_position = index / max(sensors_count - 1, 1)
            line_chart_axis.plot(
                sensor_data["timestamp"],
                sensor_data["temperature"],
                label=str(sensor_id),
                color=line_color_map(color_position),
            )
        line_chart_axis.set_title("Temperature over time")
        line_chart_axis.set_xlabel("Time")
        line_chart_axis.set_ylabel("Temperature")
        histogram_axis.hist(self.df["temperature"], bins=20, color="#A7D8F0", edgecolor="white", linewidth=0.7)
        histogram_axis.set_title("Temperature histogram")
        histogram_axis.set_xlabel("Temperature")
        histogram_axis.set_ylabel("Count")
        self.charts_canvas.draw_idle()


if __name__ == "__main__":
    app = QApplication([])
    window = TemperatureAnalysisDashboard()
    window.showMaximized()
    app.exec()

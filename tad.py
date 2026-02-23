import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class TemperatureAnalysisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.df = pd.DataFrame()
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
        table_label = QLabel("Please load data to get started.")
        table_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(table_label)
        results_tabs_widget.addTab(table_widget, "Data")
        # Level 2 widget: statistics tab
        stats_widget = QWidget()
        stats_layout = QVBoxLayout(stats_widget)
        stats_label = QLabel("Please load data to get started.")
        stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        stats_layout.addWidget(stats_label)
        results_tabs_widget.addTab(stats_widget, "Statistics")
        # Level 2 widget: visualizations tab
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_label = QLabel("Please load data to get started.")
        charts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(charts_label)
        results_tabs_widget.addTab(charts_widget, "Visualizations")
        main_layout.addWidget(results_tabs_widget)

    def load_csv(self, csv_file_path):
        self.df = pd.read_csv(csv_file_path)
        self.df = self.df[["timestamp", "sensor_id", "temperature"]]
        self.df["timestamp"] = pd.to_datetime(self.df["timestamp"])
        self.statusBar().showMessage(f"Loaded {csv_file_path} ({len(self.df)} rows).")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open CSV file", "", "CSV files (*.csv)")
        if file_path.endswith(".csv"):
            self.load_csv(file_path)

    def open_network_file(self):
        url, ok = QInputDialog.getText(self, "Load CSV from network", "CSV URL:")
        if not ok or not url.strip():
            return
        self.load_csv(url.strip())

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


if __name__ == "__main__":
    app = QApplication([])
    window = TemperatureAnalysisDashboard()
    window.showMaximized()
    app.exec()

from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QApplication,
    QGroupBox,
    QHBoxLayout,
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
        load_layout.addWidget(QPushButton("From disk"))
        load_layout.addWidget(QPushButton("From network"))
        load_layout.addWidget(QLabel("Supported formats: CSV, JSON"))
        load_layout.addStretch()
        load_save_layout.addWidget(load_frame_widget)
        # Level 2 widget: save frame
        save_frame_widget = QGroupBox("Save data")
        save_layout = QHBoxLayout(save_frame_widget)
        save_layout.addWidget(QPushButton("Save as"))
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


if __name__ == "__main__":
    app = QApplication([])
    window = TemperatureAnalysisDashboard()
    window.showMaximized()
    app.exec()

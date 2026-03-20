import base64
import io
import os
import tempfile

import markdown
import numpy as np
import pandas as pd
import pdfkit
import requests
from matplotlib import colormaps
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QDateTimeEdit,
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


class Banner(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        banner_widget = QSvgWidget("tad_banner.svg")
        banner_widget.setFixedHeight(100)
        layout.addWidget(banner_widget)


class LoadSaveSection(QWidget):
    def __init__(self, open_file_callback, open_network_callback, save_file_callback):
        super().__init__()
        layout = QHBoxLayout(self)
        # Load frame
        load_frame_widget = QGroupBox("Load data")
        load_layout = QHBoxLayout(load_frame_widget)
        load_from_disk_button = QPushButton("From disk")
        load_from_disk_button.clicked.connect(open_file_callback)
        load_layout.addWidget(load_from_disk_button)
        load_from_network_button = QPushButton("From network")
        load_from_network_button.clicked.connect(open_network_callback)
        load_layout.addWidget(load_from_network_button)
        load_layout.addWidget(QLabel("Supported formats: CSV, JSON"))
        load_layout.addStretch()
        layout.addWidget(load_frame_widget)
        # Save frame
        save_frame_widget = QGroupBox("Save data")
        save_layout = QHBoxLayout(save_frame_widget)
        save_as_button = QPushButton("Save as")
        save_as_button.clicked.connect(save_file_callback)
        save_layout.addWidget(save_as_button)
        save_layout.addWidget(QLabel("Supported formats: CSV, JSON, PDF report"))
        save_layout.addStretch()
        layout.addWidget(save_frame_widget)


class FiltersFrame(QWidget):
    def __init__(self, apply_filters_callback, reset_datetime_callback):
        super().__init__()
        layout = QVBoxLayout(self)
        # Sensor selection
        sensors_widget = QWidget()
        sensors_layout = QHBoxLayout(sensors_widget)
        sensors_layout.addWidget(QLabel("Sensors:"))
        self.sensors_values_widget = QWidget()
        self.sensors_values_layout = QHBoxLayout(self.sensors_values_widget)
        self.sensors_values_layout.setContentsMargins(0, 0, 0, 0)
        self.sensors_values_layout.setSpacing(8)
        sensors_layout.addWidget(self.sensors_values_widget)
        sensors_layout.addStretch()
        layout.addWidget(sensors_widget)
        # Date/time range
        temperature_widget = QWidget()
        temperature_layout = QHBoxLayout(temperature_widget)
        temperature_layout.addWidget(QLabel("Date/time range:"))
        self.datetime_from_label = QLabel("From:")
        self.datetime_from_label.setVisible(False)
        temperature_layout.addWidget(self.datetime_from_label)
        self.datetime_from_edit = QDateTimeEdit()
        self.datetime_from_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_from_edit.setCalendarPopup(True)
        self.datetime_from_edit.setVisible(False)
        self.datetime_from_edit.dateTimeChanged.connect(apply_filters_callback)
        temperature_layout.addWidget(self.datetime_from_edit)
        self.datetime_to_label = QLabel("To:")
        self.datetime_to_label.setVisible(False)
        temperature_layout.addWidget(self.datetime_to_label)
        self.datetime_to_edit = QDateTimeEdit()
        self.datetime_to_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_to_edit.setCalendarPopup(True)
        self.datetime_to_edit.setVisible(False)
        self.datetime_to_edit.dateTimeChanged.connect(apply_filters_callback)
        temperature_layout.addWidget(self.datetime_to_edit)
        self.reset_datetime_button = QPushButton("Reset")
        self.reset_datetime_button.setVisible(False)
        self.reset_datetime_button.clicked.connect(reset_datetime_callback)
        temperature_layout.addWidget(self.reset_datetime_button)
        temperature_layout.addStretch()
        layout.addWidget(temperature_widget)


class ResultsTabs(QTabWidget):
    def __init__(self, on_table_header_clicked):
        super().__init__()
        # Data table tab
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.table_label = QLabel("Please load data to get started.")
        self.table_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        table_layout.addWidget(self.table_label)
        self.data_table = QTableWidget()
        self.data_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.data_table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.data_table.horizontalHeader().setSortIndicatorShown(True)
        self.data_table.horizontalHeader().sectionClicked.connect(on_table_header_clicked)
        self.data_table.setVisible(False)
        table_layout.addWidget(self.data_table)
        self.addTab(table_widget, "Data")
        # Statistics tab
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
        self.addTab(stats_widget, "Statistics")
        # Visualizations tab
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        self.charts_label = QLabel("Please load data to get started.")
        self.charts_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        charts_layout.addWidget(self.charts_label)
        self.charts_canvas = ChartsCanvas()
        self.charts_canvas.setVisible(False)
        charts_layout.addWidget(self.charts_canvas)
        self.addTab(charts_widget, "Visualizations")


class TemperatureAnalysisDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.original_df = pd.DataFrame()
        self.df = pd.DataFrame()
        self.sensor_checkboxes = {}
        self.table_sort_column = None
        self.table_sort_ascending = True
        self.setCentralWidget(main_widget)
        self.setWindowTitle("TAD - Temperature Analysis Dashboard")
        self.statusBar().showMessage("Please load data to get started.")
        self.banner = Banner()
        main_layout.addWidget(self.banner)
        self.load_save_section = LoadSaveSection(self.open_file, self.open_network_file, self.save_file)
        main_layout.addWidget(self.load_save_section)
        self.filters_frame = FiltersFrame(self.apply_filters, self.reset_datetime_filters)
        main_layout.addWidget(self.filters_frame)
        self.results_tabs = ResultsTabs(self.on_table_header_clicked)
        main_layout.addWidget(self.results_tabs)

    def draw_histogram(self, axis):
        axis.hist(self.df["temperature"], bins=20, color="#A7D8F0", edgecolor="white", linewidth=0.7)
        axis.set_title("Temperature histogram")
        axis.set_xlabel("Temperature")
        axis.set_ylabel("Count")

    def draw_boxplot(self, axis):
        grouped = [sensor_data["temperature"] for _, sensor_data in self.df.groupby("sensor_id")]
        labels = [str(sensor_id) for sensor_id in self.df["sensor_id"].unique()]
        axis.boxplot(grouped, labels=labels)
        axis.set_title("Temperature boxplot by sensor")
        axis.set_xlabel("Sensor")
        axis.set_ylabel("Temperature")

    def load_csv(self, csv_file_path):
        self.original_df = pd.read_csv(csv_file_path)
        self.process_loaded_data(csv_file_path)

    def load_json(self, json_file_path):
        self.original_df = pd.read_json(json_file_path, orient="records")
        self.process_loaded_data(json_file_path)

    def on_table_header_clicked(self, logical_index):
        if self.df.empty or logical_index >= len(self.df.columns):
            return
        clicked_column = self.df.columns[logical_index]
        if self.table_sort_column == clicked_column:
            self.table_sort_ascending = not self.table_sort_ascending
        else:
            self.table_sort_column = clicked_column
            self.table_sort_ascending = True
        self.update_data_table()

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
        default_url = "https://raw.githubusercontent.com/dorezler/tad/refs/heads/main/test_data.csv"
        url, ok = QInputDialog.getText(self, "Load data from network", "Data URL:", text=default_url)
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
        self.refresh_datetime_filters()
        self.apply_filters()
        self.statusBar().showMessage(f"Loaded {data_source} ({len(self.original_df)} rows).")

    def refresh_datetime_filters(self):
        if self.original_df.empty:
            self.filters_frame.datetime_from_label.setVisible(False)
            self.filters_frame.datetime_from_edit.setVisible(False)
            self.filters_frame.datetime_to_label.setVisible(False)
            self.filters_frame.datetime_to_edit.setVisible(False)
            self.filters_frame.reset_datetime_button.setVisible(False)
            self.filters_frame.datetime_from_edit.blockSignals(True)
            self.filters_frame.datetime_to_edit.blockSignals(True)
            self.filters_frame.datetime_from_edit.blockSignals(False)
            self.filters_frame.datetime_to_edit.blockSignals(False)
            return
        min_timestamp = self.original_df["timestamp"].min()
        max_timestamp = self.original_df["timestamp"].max()
        min_qdatetime = self.filters_frame.datetime_from_edit.dateTimeFromText(
            min_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )
        max_qdatetime = self.filters_frame.datetime_to_edit.dateTimeFromText(
            max_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        )
        self.filters_frame.datetime_from_edit.blockSignals(True)
        self.filters_frame.datetime_to_edit.blockSignals(True)
        self.filters_frame.datetime_from_edit.setMinimumDateTime(min_qdatetime)
        self.filters_frame.datetime_from_edit.setMaximumDateTime(max_qdatetime)
        self.filters_frame.datetime_from_edit.setDateTime(min_qdatetime)
        self.filters_frame.datetime_to_label.setVisible(True)
        self.filters_frame.datetime_to_edit.setVisible(True)
        self.filters_frame.datetime_to_edit.setMinimumDateTime(min_qdatetime)
        self.filters_frame.datetime_to_edit.setMaximumDateTime(max_qdatetime)
        self.filters_frame.datetime_to_edit.setDateTime(max_qdatetime)
        self.filters_frame.datetime_from_label.setVisible(True)
        self.filters_frame.datetime_from_edit.setVisible(True)
        self.filters_frame.datetime_from_edit.blockSignals(False)
        self.filters_frame.datetime_to_edit.blockSignals(False)
        self.filters_frame.reset_datetime_button.setVisible(True)

    def refresh_sensor_filters(self):
        clear_layout(self.filters_frame.sensors_values_layout)
        self.sensor_checkboxes = {}
        if self.original_df.empty:
            return
        for sensor_id in sorted(self.original_df["sensor_id"].dropna().unique()):
            checkbox = QCheckBox(str(sensor_id))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.apply_filters)
            self.filters_frame.sensors_values_layout.addWidget(checkbox)
            self.sensor_checkboxes[sensor_id] = checkbox

    def reset_datetime_filters(self):
        if self.original_df.empty:
            return
        self.refresh_datetime_filters()
        self.apply_filters()

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
            if (
                not self.df.empty
                and not self.filters_frame.datetime_from_edit.isHidden()
                and not self.filters_frame.datetime_to_edit.isHidden()
            ):
                from_timestamp = pd.to_datetime(
                    self.filters_frame.datetime_from_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                )
                to_timestamp = pd.to_datetime(
                    self.filters_frame.datetime_to_edit.dateTime().toString("yyyy-MM-dd HH:mm:ss")
                )
                self.df = self.df[(self.df["timestamp"] >= from_timestamp) & (self.df["timestamp"] <= to_timestamp)]
        self.update_data_table()
        self.update_statistics_label()
        self.update_visualizations()

    def export_to_md(self, file_path, n_rows=5, include_stats=True, include_viz=True):
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# TAD Data Export\n\n")
            f.write(f"Number of rows: {len(self.df)}\n\n")
            # Table
            if not self.df.empty:
                f.write(self.df.head(n_rows).to_markdown(index=False))
                if len(self.df) > n_rows:
                    f.write(f"\n\n(only first {n_rows} rows)\n")
            else:
                f.write("No data to display.\n")
            # Statistics
            if include_stats and not self.df.empty:
                f.write("\n\n## Statistics\n")
                f.write("\nGlobal statistics (all sensors):\n\n")
                f.write(
                    "```\n" + self.df["temperature"].describe().to_string(float_format=lambda v: f"{v:.2f}") + "\n```\n"
                )
                f.write("\nStatistics for each filtered sensor:\n\n")
                for sensor_id, sensor_data in self.df.groupby("sensor_id"):
                    f.write(f"\nSensor {sensor_id}:\n")
                    f.write(
                        "```\n"
                        + sensor_data["temperature"].describe().to_string(float_format=lambda v: f"{v:.2f}")
                        + "\n```\n"
                    )
            # Visualizations
            if include_viz and not self.df.empty:
                f.write("\n\n## Visualizations\n")
                # Data range
                min_date = self.df["timestamp"].min()
                max_date = self.df["timestamp"].max()
                data_range = f"Filtered data range: {min_date.strftime('%Y-%m-%d %H:%M:%S')} - {max_date.strftime('%Y-%m-%d %H:%M:%S')}"
                f.write(f"\n*{data_range}*\n")
                # Line chart
                fig = Figure(figsize=(8, 4), tight_layout=True)
                ax = fig.add_subplot(1, 1, 1)
                for sensor_id, sensor_data in self.df.groupby("sensor_id"):
                    ax.plot(sensor_data["timestamp"], sensor_data["temperature"], label=str(sensor_id))
                ax.set_title("Temperature over time")
                ax.set_xlabel("Time")
                ax.set_ylabel("Temperature")
                ax.legend()
                f.write(f"\n{fig_to_base64_img(fig)}\n")
                # Histogram
                fig2 = Figure(figsize=(8, 4), tight_layout=True)
                ax2 = fig2.add_subplot(1, 1, 1)
                self.draw_histogram(ax2)
                f.write(f"\n{fig_to_base64_img(fig2)}\n")
                # Boxplot
                fig3 = Figure(figsize=(8, 4), tight_layout=True)
                ax3 = fig3.add_subplot(1, 1, 1)
                self.draw_boxplot(ax3)
                f.write(f"\n{fig_to_base64_img(fig3)}\n")
                # Heatmap
                fig4 = Figure(figsize=(8, 4), tight_layout=True)
                ax4 = fig4.add_subplot(1, 1, 1)
                heatmap_data = self.df.pivot(index="sensor_id", columns="timestamp", values="temperature")
                im = ax4.imshow(heatmap_data, aspect="auto", cmap="coolwarm")
                ax4.set_title("Temperature heatmap")
                ax4.set_xlabel("Time")
                ax4.set_ylabel("Sensor")
                fig4.colorbar(im, ax=ax4)
                f.write(f"\n{fig_to_base64_img(fig4)}\n")
            # Footer
            f.write("\n---\nReport generated automatically by TAD.\n")

    def export_md_to_pdf(self, md_path, pdf_path):
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        html_content = markdown.markdown(md_content, extensions=["tables"])
        style = """<style>table {border-collapse: collapse;} th, td {border: 1px solid #888; padding: 4px;} th {background: #eee;}</style>"""
        html_full = f"<html><head>{style}</head><body>{html_content}</body></html>"
        pdfkit.from_string(html_full, pdf_path)

    def save_file(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save data file", "", "CSV files (*.csv);;JSON files (*.json);;Markdown (*.md);;PDF report (*.pdf)"
        )
        if not file_path:
            return
        if selected_filter.startswith("JSON") or file_path.lower().endswith(".json"):
            file_path = ensure_extension(file_path, ".json")
            self.df.to_json(file_path, date_format="iso", indent=2, orient="records")
        elif selected_filter.startswith("Markdown") or file_path.lower().endswith(".md"):
            file_path = ensure_extension(file_path, ".md")
            self.export_to_md(file_path, n_rows=5, include_stats=True, include_viz=True)
            self.statusBar().showMessage(f"Saved data to {file_path} (markdown)")
        elif selected_filter.startswith("PDF") or file_path.lower().endswith(".pdf"):
            file_path = ensure_extension(file_path, ".pdf")
            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as tmp_md:
                self.export_to_md(tmp_md.name, n_rows=5, include_stats=True, include_viz=True)
                tmp_md_path = tmp_md.name
            self.export_md_to_pdf(tmp_md_path, file_path)
            os.remove(tmp_md_path)
            self.statusBar().showMessage(f"Saved data to {file_path} (PDF)")
        else:
            file_path = ensure_extension(file_path, ".csv")
            self.df.to_csv(file_path, index=False)
        if not (selected_filter.startswith("PDF") or file_path.lower().endswith(".pdf")):
            self.statusBar().showMessage(f"Saved data to {file_path} ({len(self.df)} rows).")

    def update_data_table(self):
        if self.df.empty:
            self.results_tabs.table_label.setVisible(True)
            self.results_tabs.table_label.setText("No data for current filters.")
            self.results_tabs.data_table.setVisible(False)
            return
        display_df = self.df
        if self.table_sort_column in self.df.columns:
            display_df = self.df.sort_values(self.table_sort_column, ascending=self.table_sort_ascending)
        else:
            self.table_sort_column = None
        self.results_tabs.table_label.setVisible(False)
        self.results_tabs.data_table.setVisible(True)
        self.results_tabs.data_table.setRowCount(len(display_df))
        self.results_tabs.data_table.setColumnCount(len(display_df.columns))
        self.results_tabs.data_table.setHorizontalHeaderLabels([str(column) for column in display_df.columns])
        if self.table_sort_column in display_df.columns:
            sort_column_index = display_df.columns.get_loc(self.table_sort_column)
            sort_order = Qt.SortOrder.AscendingOrder if self.table_sort_ascending else Qt.SortOrder.DescendingOrder
            self.results_tabs.data_table.horizontalHeader().setSortIndicator(sort_column_index, sort_order)
        for row_index, (_, row) in enumerate(display_df.iterrows()):
            for column_index, value in enumerate(row):
                self.results_tabs.data_table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def update_statistics_label(self):
        if self.df.empty:
            self.results_tabs.stats_label.setVisible(True)
            if self.original_df.empty:
                self.results_tabs.stats_label.setText("Please load data to get started.")
            else:
                self.results_tabs.stats_label.setText("No data for current filters.")
            self.results_tabs.stats_scroll_area.setVisible(False)
            clear_layout(self.results_tabs.stats_frames_layout)
            return
        self.results_tabs.stats_label.setVisible(False)
        self.results_tabs.stats_scroll_area.setVisible(True)
        clear_layout(self.results_tabs.stats_frames_layout)

        global_stats_box = QGroupBox("Global statistics (all sensors)")
        global_stats_layout = QVBoxLayout(global_stats_box)
        global_stats_label = QLabel(
            self.df["temperature"].describe().to_string(float_format=lambda value: f"{value:.1f}")
        )
        global_stats_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        global_stats_layout.addWidget(global_stats_label)
        self.results_tabs.stats_frames_layout.addWidget(global_stats_box, 0, 0, 1, 4)

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
            self.results_tabs.stats_frames_layout.addWidget(sensor_stats_box, row_index, column_index)

    def update_visualizations(self):
        if self.df.empty:
            self.results_tabs.charts_label.setVisible(True)
            if self.original_df.empty:
                self.results_tabs.charts_label.setText("Please load data to get started.")
            else:
                self.results_tabs.charts_label.setText("No data for current filters.")
            self.results_tabs.charts_canvas.setVisible(False)
            return
        self.results_tabs.charts_label.setVisible(False)
        self.results_tabs.charts_canvas.setVisible(True)
        figure = self.results_tabs.charts_canvas.figure
        figure.clear()
        line_chart_axis = figure.add_subplot(2, 2, 1)
        histogram_axis = figure.add_subplot(2, 2, 2)
        boxplot_axis = figure.add_subplot(2, 2, 3)
        heatmap_axis = figure.add_subplot(2, 2, 4)
        line_chart_data = self.df.sort_values("timestamp")
        line_color_map = colormaps["tab10"]
        sensors_count = line_chart_data["sensor_id"].nunique()
        anomaly_label_added = False
        for index, (sensor_id, sensor_data) in enumerate(line_chart_data.groupby("sensor_id")):
            color_position = index / max(sensors_count - 1, 1)
            line_chart_axis.plot(
                sensor_data["timestamp"],
                sensor_data["temperature"],
                label=str(sensor_id),
                color=line_color_map(color_position),
            )
            sensor_std = sensor_data["temperature"].std()
            sensor_mean = sensor_data["temperature"].mean()
            anomalies = sensor_data[(sensor_data["temperature"] - sensor_mean).abs() > (2 * sensor_std)]
            if not anomalies.empty:
                line_chart_axis.scatter(
                    anomalies["timestamp"],
                    anomalies["temperature"],
                    color="red",
                    marker="x",
                    label="Anomaly" if not anomaly_label_added else None,
                )
                anomaly_label_added = True
        line_chart_axis.set_title("Temperature over time")
        line_chart_axis.set_xlabel("Time")
        line_chart_axis.set_ylabel("Temperature")
        unique_timestamps = line_chart_data["timestamp"].unique()
        x_ticks_indices = np.linspace(0, len(unique_timestamps) - 1, 16).astype(int)
        x_tick_labels = [unique_timestamps[i].strftime("%d %b\n%H:%M") for i in x_ticks_indices]
        line_chart_axis.set_xticks(unique_timestamps[x_ticks_indices])
        line_chart_axis.set_xticklabels(x_tick_labels, rotation=90, fontsize=6)
        line_chart_axis.legend()
        self.draw_histogram(histogram_axis)
        self.draw_boxplot(boxplot_axis)
        heatmap_data = self.df.pivot(index="sensor_id", columns="timestamp", values="temperature")
        heatmap_axis.imshow(heatmap_data, aspect="auto", cmap="coolwarm")
        heatmap_axis.set_title("Temperature heatmap")
        heatmap_axis.set_xlabel("Time")
        heatmap_axis.set_ylabel("Sensor")
        x_ticks_indices = np.linspace(0, len(heatmap_data.columns) - 1, 20).astype(int)
        x_tick_labels = [heatmap_data.columns[i].strftime("%d %b\n%H:%M") for i in x_ticks_indices]
        heatmap_axis.set_xticks(x_ticks_indices)
        heatmap_axis.set_xticklabels(x_tick_labels, rotation=90, fontsize=6)
        heatmap_axis.set_yticks(np.arange(len(heatmap_data.index)))
        heatmap_axis.set_yticklabels([str(idx) for idx in heatmap_data.index], fontsize=8)
        self.results_tabs.charts_canvas.draw_idle()


def clear_layout(layout):
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def ensure_extension(file_path, extension):
    if not file_path.lower().endswith(extension):
        return f"{file_path}{extension}"
    return file_path


def fig_to_base64_img(fig, width=600):
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return f'<img src="data:image/png;base64,{img_base64}" width="{width}"/>'


if __name__ == "__main__":
    app = QApplication([])
    window = TemperatureAnalysisDashboard()
    window.showMaximized()
    app.exec()

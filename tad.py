import io

import numpy as np
import pandas as pd
import requests
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)
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
        layout = QHBoxLayout(self)
        # Sensor selection
        self.sensors_widget = QWidget()
        sensors_layout = QHBoxLayout(self.sensors_widget)
        sensors_layout.addWidget(QLabel("Sensors:"))
        self.sensors_values_widget = QWidget()
        self.sensors_values_layout = QHBoxLayout(self.sensors_values_widget)
        self.sensors_values_layout.setContentsMargins(0, 0, 0, 0)
        self.sensors_values_layout.setSpacing(8)
        sensors_layout.addWidget(self.sensors_values_widget)
        self.sensors_widget.setVisible(False)
        layout.addWidget(self.sensors_widget)
        # Date/time range
        self.datetime_range_widget = QWidget()
        datetime_range_layout = QHBoxLayout(self.datetime_range_widget)
        datetime_range_layout.addWidget(QLabel("Date/time range:"))
        self.datetime_from_label = QLabel("From:")
        self.datetime_from_label.setVisible(False)
        datetime_range_layout.addWidget(self.datetime_from_label)
        self.datetime_from_edit = QDateTimeEdit()
        self.datetime_from_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_from_edit.setCalendarPopup(True)
        self.datetime_from_edit.setVisible(False)
        self.datetime_from_edit.dateTimeChanged.connect(apply_filters_callback)
        datetime_range_layout.addWidget(self.datetime_from_edit)
        self.datetime_to_label = QLabel("To:")
        self.datetime_to_label.setVisible(False)
        datetime_range_layout.addWidget(self.datetime_to_label)
        self.datetime_to_edit = QDateTimeEdit()
        self.datetime_to_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.datetime_to_edit.setCalendarPopup(True)
        self.datetime_to_edit.setVisible(False)
        self.datetime_to_edit.dateTimeChanged.connect(apply_filters_callback)
        datetime_range_layout.addWidget(self.datetime_to_edit)
        self.reset_datetime_button = QPushButton("Reset")
        self.reset_datetime_button.setVisible(False)
        self.reset_datetime_button.clicked.connect(reset_datetime_callback)
        datetime_range_layout.addWidget(self.reset_datetime_button)
        self.datetime_range_widget.setVisible(False)
        layout.addWidget(self.datetime_range_widget)
        layout.addStretch()


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

    def draw_boxplot(self, axis):
        grouped = [sensor_data["temperature"] for _, sensor_data in self.df.groupby("sensor_id")]
        labels = [str(sensor_id) for sensor_id in self.df["sensor_id"].unique()]
        axis.boxplot(grouped, tick_labels=labels)
        axis.set_title("Temperature boxplot by sensor")
        axis.set_xlabel("Sensor")
        axis.set_ylabel("Temperature")

    def draw_heatmap(self, axis):
        heatmap_data = self.df.pivot(index="sensor_id", columns="timestamp", values="temperature")
        image = axis.imshow(heatmap_data, aspect="auto", cmap="coolwarm")
        axis.set_title("Temperature heatmap")
        axis.set_xlabel("Time")
        axis.set_ylabel("Sensor")
        axis.figure.colorbar(image, ax=axis)
        axis.set_yticks(np.arange(len(heatmap_data.index)))
        axis.set_yticklabels([str(idx) for idx in heatmap_data.index], fontsize=8)
        return heatmap_data

    def draw_histogram(self, axis):
        temperature_values = self.df["temperature"].dropna()
        min_temperature = np.floor(temperature_values.min() * 2) / 2
        max_temperature = np.ceil(temperature_values.max() * 2) / 2
        bin_edges = np.arange(min_temperature, max_temperature + 0.5, 0.5)
        if len(bin_edges) < 2:
            bin_edges = np.array([min_temperature, min_temperature + 0.5])
        axis.hist(temperature_values, bins=bin_edges, edgecolor="white")
        tick_start = np.floor(min_temperature)
        tick_end = np.ceil(max_temperature)
        axis.set_xticks(np.arange(tick_start, tick_end + 1, 1))
        axis.set_title("Temperature histogram")
        axis.set_xlabel("Temperature")
        axis.set_ylabel("Count")

    def draw_line_chart(self, axis, include_anomalies=False):
        line_chart_data = self.df.sort_values("timestamp")
        if include_anomalies:
            anomaly_label_added = False
            for sensor_id, sensor_data in line_chart_data.groupby("sensor_id"):
                axis.plot(
                    sensor_data["timestamp"],
                    sensor_data["temperature"],
                    label=str(sensor_id),
                )
                sensor_std = sensor_data["temperature"].std()
                sensor_mean = sensor_data["temperature"].mean()
                anomalies = sensor_data[(sensor_data["temperature"] - sensor_mean).abs() > (2 * sensor_std)]
                if not anomalies.empty:
                    axis.scatter(
                        anomalies["timestamp"],
                        anomalies["temperature"],
                        marker="x",
                        label="Anomaly" if not anomaly_label_added else None,
                    )
                    anomaly_label_added = True
        else:
            for sensor_id, sensor_data in line_chart_data.groupby("sensor_id"):
                axis.plot(sensor_data["timestamp"], sensor_data["temperature"], label=str(sensor_id))
        axis.set_title("Temperature over time")
        axis.set_xlabel("Time")
        axis.set_ylabel("Temperature")
        legend_handles, legend_labels = axis.get_legend_handles_labels()
        if "Anomaly" in legend_labels:
            anomaly_index = legend_labels.index("Anomaly")
            anomaly_handle = legend_handles.pop(anomaly_index)
            legend_labels.pop(anomaly_index)
            legend_handles.append(anomaly_handle)
            legend_labels.append("Anomaly")
        axis.legend(legend_handles, legend_labels, loc="upper right")
        return line_chart_data

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
            self.filters_frame.datetime_range_widget.setVisible(False)
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
        self.filters_frame.datetime_range_widget.setVisible(True)
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
            self.filters_frame.sensors_widget.setVisible(False)
            return
        self.filters_frame.sensors_widget.setVisible(True)
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

    def append_pdf_stats(self, story, styles):
        story.append(Spacer(1, 12))
        story.append(Paragraph("Statistics", styles["Heading2"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph("Global statistics (all filtered sensors)", styles["Heading3"]))
        story.append(
            Preformatted(
                self.df["temperature"].describe().to_string(float_format=lambda value: f"{value:.2f}"),
                styles["Code"],
            )
        )
        for sensor_id, sensor_data in self.df.groupby("sensor_id"):
            story.append(Spacer(1, 6))
            story.append(Paragraph(f"Sensor {sensor_id}", styles["Heading3"]))
            story.append(
                Preformatted(
                    sensor_data["temperature"].describe().to_string(float_format=lambda value: f"{value:.2f}"),
                    styles["Code"],
                )
            )

    def append_pdf_visualizations(self, story, styles, doc):
        story.append(PageBreak())
        story.append(Paragraph("Visualizations", styles["Heading2"]))
        story.append(Spacer(1, 8))
        available_width = A4[0] - doc.leftMargin - doc.rightMargin
        chart_width = available_width
        chart_height = chart_width * 0.5
        for index, (caption, figure) in enumerate(self.build_pdf_figures(), start=1):
            chart_buffer = fig_to_png_buffer(figure)
            story.append(Image(chart_buffer, width=chart_width, height=chart_height))
            story.append(Spacer(1, 2))
            story.append(Paragraph(f"Fig. {index}. {caption}.", styles["Italic"]))
            story.append(Spacer(1, 8))

    def build_pdf_figures(self):
        figures = []
        fig = Figure(figsize=(8, 4), tight_layout=True)
        ax = fig.add_subplot(1, 1, 1)
        self.draw_line_chart(ax, include_anomalies=True)
        figures.append(("Temperature over time", fig))
        fig2 = Figure(figsize=(8, 4), tight_layout=True)
        ax2 = fig2.add_subplot(1, 1, 1)
        self.draw_histogram(ax2)
        figures.append(("Temperature histogram", fig2))
        fig3 = Figure(figsize=(8, 4), tight_layout=True)
        ax3 = fig3.add_subplot(1, 1, 1)
        self.draw_boxplot(ax3)
        figures.append(("Temperature boxplot by sensor", fig3))
        fig4 = Figure(figsize=(8, 4), tight_layout=True)
        ax4 = fig4.add_subplot(1, 1, 1)
        self.draw_heatmap(ax4)
        figures.append(("Temperature heatmap", fig4))
        return figures

    def create_pdf_doc(self, pdf_path):
        return SimpleDocTemplate(
            pdf_path,
            pagesize=A4,
            leftMargin=15 * mm,
            rightMargin=15 * mm,
            topMargin=15 * mm,
            bottomMargin=15 * mm,
        )

    def export_pdf_report(self, pdf_path, include_stats=True, include_viz=True):
        styles = getSampleStyleSheet()
        doc = self.create_pdf_doc(pdf_path)
        story = [Paragraph("TAD Data Export", styles["Title"]), Spacer(1, 8)]
        story.append(Spacer(1, 4))
        if self.df.empty:
            story.append(Paragraph("No data to display.", styles["Normal"]))
        else:
            min_date = self.df["timestamp"].min()
            max_date = self.df["timestamp"].max()
            story.append(
                Paragraph(
                    f"Filtered data range: {min_date.strftime('%Y-%m-%d %H:%M:%S')} - {max_date.strftime('%Y-%m-%d %H:%M:%S')}",
                    styles["Italic"],
                )
            )
            story.append(Spacer(1, 10))
        if include_stats and not self.df.empty:
            self.append_pdf_stats(story, styles)
        if include_viz and not self.df.empty:
            self.append_pdf_visualizations(story, styles, doc)
        story.append(Spacer(1, 12))
        story.append(Paragraph("Report generated automatically by TAD.", styles["Italic"]))
        doc.build(story)

    def save_file(self):
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Save data file", "", "CSV files (*.csv);;JSON files (*.json);;PDF report (*.pdf)"
        )
        if not file_path:
            return
        if selected_filter.startswith("JSON") or file_path.lower().endswith(".json"):
            file_path = ensure_extension(file_path, ".json")
            self.df.to_json(file_path, date_format="iso", indent=2, orient="records")
        elif selected_filter.startswith("PDF") or file_path.lower().endswith(".pdf"):
            file_path = ensure_extension(file_path, ".pdf")
            self.export_pdf_report(file_path, include_stats=True, include_viz=True)
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

        global_stats_box = QGroupBox("Global statistics (all filtered sensors)")
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
        line_chart_data = self.draw_line_chart(line_chart_axis, include_anomalies=True)
        unique_timestamps = line_chart_data["timestamp"].unique()
        x_ticks_indices = np.linspace(0, len(unique_timestamps) - 1, 16).astype(int)
        x_tick_labels = [unique_timestamps[i].strftime("%d %b\n%H:%M") for i in x_ticks_indices]
        line_chart_axis.set_xticks(unique_timestamps[x_ticks_indices])
        line_chart_axis.set_xticklabels(x_tick_labels, rotation=90, fontsize=6)
        self.draw_histogram(histogram_axis)
        self.draw_boxplot(boxplot_axis)
        self.draw_heatmap(heatmap_axis)
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


def fig_to_png_buffer(fig):
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png")
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    app = QApplication([])
    window = TemperatureAnalysisDashboard()
    window.showMaximized()
    app.exec()

"""TAD – Temperature Analysis Dashboard: load, filter and visualize temperature sensor data."""

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from constants import (
    COLUMN_SENSOR_ID,
    COLUMN_TEMPERATURE,
    COLUMN_TIMESTAMP,
    DATETIME_FORMAT_PY,
    DATETIME_FORMAT_QT,
    FILE_DIALOG_OPEN_DATA_FILE_FILTER,
    FILE_DIALOG_OPEN_DATA_FILE_TITLE,
    FILE_DIALOG_SAVE_DATA_FILE_FILTER,
    FILE_DIALOG_SAVE_DATA_FILE_TITLE,
    FILE_EXT_CSV,
    FILE_EXT_JSON,
    FILE_EXT_PDF,
    MESSAGE_INITIAL_DATA,
    MESSAGE_NO_DATA_FOR_FILTERS,
    NETWORK_DIALOG_DEFAULT_DATA_URL,
    NETWORK_DIALOG_PROMPT,
    NETWORK_DIALOG_TITLE,
    PDF_GLOBAL_STATS_TITLE,
    PDF_SENSOR_TITLE_TEMPLATE,
    STATUS_LOAD_TEMPLATE,
    STATUS_NETWORK_LOAD_FAILED_TEMPLATE,
    STATUS_READY_MESSAGE,
    STATUS_SAVE_PDF_TEMPLATE,
    STATUS_SAVE_ROWS_TEMPLATE,
    STATISTICS_COLUMNS,
    WINDOW_TITLE,
)
from data_io import (
    load_dataframe_from_csv,
    load_dataframe_from_json,
    load_dataframe_from_url,
    normalize_loaded_data,
    save_dataframe,
)
from visualizations import (
    configure_heatmap_xticks,
    configure_line_chart_xticks,
    draw_boxplot,
    draw_heatmap,
    draw_histogram,
    draw_line_chart,
)
from widgets import (
    Banner,
    FiltersFrame,
    LoadSaveSection,
    ResultsTabs,
    build_stats_box,
    clear_layout,
    set_datetime_filter_bounds,
)


class TemperatureAnalysisDashboard(QMainWindow):  # pylint: disable=too-many-instance-attributes,too-many-public-methods
    """Main application window orchestrating data loading, filtering and display."""

    # Setup

    def __init__(self):
        """Initialize state variables and assemble the central widget layout."""
        super().__init__()
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        self.original_df = pd.DataFrame()
        self.df = pd.DataFrame()
        self.sensor_checkboxes = {}
        self.table_sort_column = None
        self.table_sort_ascending = True
        self.setCentralWidget(main_widget)
        self.setWindowTitle(WINDOW_TITLE)
        self.statusBar().showMessage(STATUS_READY_MESSAGE)
        self.banner = Banner()
        main_layout.addWidget(self.banner)
        self.load_save_section = LoadSaveSection(self.open_file, self.open_network_file, self.save_file)
        main_layout.addWidget(self.load_save_section)
        self.filters_frame = FiltersFrame(self.apply_filters, self.reset_datetime_filters)
        main_layout.addWidget(self.filters_frame)
        self.results_tabs = ResultsTabs(self.on_table_header_clicked)
        main_layout.addWidget(self.results_tabs)

    # UI actions

    def open_file(self):
        """Open a file-chooser dialog and load the selected CSV or JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            FILE_DIALOG_OPEN_DATA_FILE_TITLE,
            "",
            FILE_DIALOG_OPEN_DATA_FILE_FILTER,
        )
        if not file_path:
            return
        if file_path.lower().endswith(FILE_EXT_CSV):
            self.original_df = load_dataframe_from_csv(file_path)
            self.process_loaded_data(file_path)
        elif file_path.lower().endswith(FILE_EXT_JSON):
            self.original_df = load_dataframe_from_json(file_path)
            self.process_loaded_data(file_path)

    def open_network_file(self):
        """Prompt the user for a URL, download the data, and load it into the dashboard."""
        default_url = NETWORK_DIALOG_DEFAULT_DATA_URL
        url, ok = QInputDialog.getText(self, NETWORK_DIALOG_TITLE, NETWORK_DIALOG_PROMPT, text=default_url)
        if not ok or not url.strip():
            return
        url = url.strip()
        try:
            self.original_df = load_dataframe_from_url(url)
        except RuntimeError as error:
            self.statusBar().showMessage(STATUS_NETWORK_LOAD_FAILED_TEMPLATE.format(error=error))
            return
        self.process_loaded_data(url)

    def save_file(self):
        """Open a save dialog and export the filtered data to CSV, JSON or PDF."""
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            FILE_DIALOG_SAVE_DATA_FILE_TITLE,
            "",
            FILE_DIALOG_SAVE_DATA_FILE_FILTER,
        )
        if not file_path:
            return
        file_path, saved_format = save_dataframe(self.df, file_path, selected_filter)
        if saved_format == FILE_EXT_PDF:
            self.statusBar().showMessage(STATUS_SAVE_PDF_TEMPLATE.format(file_path=file_path))
        else:
            self.statusBar().showMessage(STATUS_SAVE_ROWS_TEMPLATE.format(file_path=file_path, rows=len(self.df)))

    def on_table_header_clicked(self, logical_index):
        """Toggle ascending/descending sort when a table column header is clicked."""
        if self.df.empty or logical_index >= len(self.df.columns):
            return
        clicked_column = self.df.columns[logical_index]
        if self.table_sort_column == clicked_column:
            self.table_sort_ascending = not self.table_sort_ascending
        else:
            self.table_sort_column = clicked_column
            self.table_sort_ascending = True
        self.update_data_table()

    # UI action helpers

    def process_loaded_data(self, data_source):
        """Normalize columns, rebuild filters, apply them, and update the status bar."""
        self.original_df = normalize_loaded_data(self.original_df)
        self.refresh_sensor_filters()
        self.refresh_datetime_filters()
        self.apply_filters()
        self.statusBar().showMessage(STATUS_LOAD_TEMPLATE.format(data_source=data_source, rows=len(self.original_df)))

    # Filters

    def apply_filters(self):
        """Filter the working `DataFrame` by active sensors and the chosen date/time range."""
        if self.original_df.empty:
            self.df = self.original_df.copy()
        else:
            selected_sensors = [
                sensor_id for sensor_id, checkbox in self.sensor_checkboxes.items() if checkbox.isChecked()
            ]
            if selected_sensors:
                self.df = self.original_df[self.original_df[COLUMN_SENSOR_ID].isin(selected_sensors)].copy()
            else:
                self.df = self.original_df.iloc[0:0].copy()
            self.apply_datetime_filter()
        self.update_data_table()
        self.update_statistics_label()
        self.update_visualizations()

    def refresh_datetime_filters(self):
        """Show or hide date/time picker controls and set their bounds from the loaded data."""
        dt_filter = self.filters_frame.datetime_range_filter
        if self.original_df.empty:
            dt_filter.setVisible(False)
            dt_filter.from_label.setVisible(False)
            dt_filter.from_edit.setVisible(False)
            dt_filter.to_label.setVisible(False)
            dt_filter.to_edit.setVisible(False)
            dt_filter.reset_button.setVisible(False)
            dt_filter.from_edit.blockSignals(True)
            dt_filter.to_edit.blockSignals(True)
            dt_filter.from_edit.blockSignals(False)
            dt_filter.to_edit.blockSignals(False)
            return
        dt_filter.setVisible(True)
        min_timestamp = self.original_df[COLUMN_TIMESTAMP].min()
        max_timestamp = self.original_df[COLUMN_TIMESTAMP].max()
        min_qdatetime = dt_filter.from_edit.dateTimeFromText(min_timestamp.strftime(DATETIME_FORMAT_PY))
        max_qdatetime = dt_filter.to_edit.dateTimeFromText(max_timestamp.strftime(DATETIME_FORMAT_PY))
        set_datetime_filter_bounds(dt_filter, min_qdatetime, max_qdatetime)

    def refresh_sensor_filters(self):
        """Rebuild the sensor checkbox list from unique sensor IDs in the loaded data."""
        clear_layout(self.filters_frame.sensor_filter.values_layout)
        self.sensor_checkboxes = {}
        if self.original_df.empty:
            self.filters_frame.setVisible(False)
            self.filters_frame.sensor_filter.setVisible(False)
            return
        self.filters_frame.setVisible(True)
        self.filters_frame.sensor_filter.setVisible(True)
        for sensor_id in sorted(self.original_df[COLUMN_SENSOR_ID].dropna().unique()):
            checkbox = QCheckBox(str(sensor_id))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self.apply_filters)
            self.filters_frame.sensor_filter.values_layout.addWidget(checkbox)
            self.sensor_checkboxes[sensor_id] = checkbox

    def reset_datetime_filters(self):
        """Reset the date/time range to match the full extent of the loaded data."""
        if self.original_df.empty:
            return
        self.refresh_datetime_filters()
        self.apply_filters()

    # Filters helpers

    def apply_datetime_filter(self):
        """Narrow `self.df` to the date/time range currently set in the picker widgets."""
        dt_filter = self.filters_frame.datetime_range_filter
        if not self.df.empty and not dt_filter.from_edit.isHidden() and not dt_filter.to_edit.isHidden():
            from_timestamp = pd.to_datetime(dt_filter.from_edit.dateTime().toString(DATETIME_FORMAT_QT))
            to_timestamp = pd.to_datetime(dt_filter.to_edit.dateTime().toString(DATETIME_FORMAT_QT))
            self.df = self.df[
                (self.df[COLUMN_TIMESTAMP] >= from_timestamp) & (self.df[COLUMN_TIMESTAMP] <= to_timestamp)
            ]

    # View updates

    def update_data_table(self):
        """Populate the table widget with rows from the filtered `DataFrame`."""
        data_tab = self.results_tabs.data_tab
        if self.df.empty:
            data_tab.label.setVisible(True)
            data_tab.label.setText(MESSAGE_NO_DATA_FOR_FILTERS)
            data_tab.table.setVisible(False)
            return
        display_df = self.df
        if self.table_sort_column in self.df.columns:
            display_df = self.df.sort_values(self.table_sort_column, ascending=self.table_sort_ascending)
        else:
            self.table_sort_column = None
        data_tab.label.setVisible(False)
        data_tab.table.setVisible(True)
        data_tab.table.setRowCount(len(display_df))
        data_tab.table.setColumnCount(len(display_df.columns))
        data_tab.table.setHorizontalHeaderLabels([str(column) for column in display_df.columns])
        self.sync_sort_indicator(data_tab.table, display_df)
        for row_index, (_, row) in enumerate(display_df.iterrows()):
            for column_index, value in enumerate(row):
                data_tab.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def update_statistics_label(self):
        """Rebuild the statistics scroll area with global and per-sensor stat boxes."""
        stats_tab = self.results_tabs.stats_tab
        if self.df.empty:
            stats_tab.label.setVisible(True)
            if self.original_df.empty:
                stats_tab.label.setText(MESSAGE_INITIAL_DATA)
            else:
                stats_tab.label.setText(MESSAGE_NO_DATA_FOR_FILTERS)
            stats_tab.scroll_area.setVisible(False)
            clear_layout(stats_tab.frames_layout)
            return
        stats_tab.label.setVisible(False)
        stats_tab.scroll_area.setVisible(True)
        clear_layout(stats_tab.frames_layout)

        global_stats_box = build_stats_box(PDF_GLOBAL_STATS_TITLE, self.df[COLUMN_TEMPERATURE])
        stats_tab.frames_layout.addWidget(global_stats_box, 0, 0, 1, STATISTICS_COLUMNS)

        for index, (sensor_id, sensor_data) in enumerate(self.df.groupby(COLUMN_SENSOR_ID)):
            sensor_stats_box = build_stats_box(
                PDF_SENSOR_TITLE_TEMPLATE.format(sensor_id=sensor_id),
                sensor_data[COLUMN_TEMPERATURE],
            )
            row_index = (index // STATISTICS_COLUMNS) + 1
            column_index = index % STATISTICS_COLUMNS
            stats_tab.frames_layout.addWidget(sensor_stats_box, row_index, column_index)

    def update_visualizations(self):
        """Redraw all four chart subplots on the visualizations canvas."""
        viz_tab = self.results_tabs.viz_tab
        if self.df.empty:
            viz_tab.label.setVisible(True)
            if self.original_df.empty:
                viz_tab.label.setText(MESSAGE_INITIAL_DATA)
            else:
                viz_tab.label.setText(MESSAGE_NO_DATA_FOR_FILTERS)
            viz_tab.canvas.setVisible(False)
            return
        viz_tab.label.setVisible(False)
        viz_tab.canvas.setVisible(True)
        figure = viz_tab.canvas.figure
        figure.clear()
        line_chart_axis = figure.add_subplot(2, 2, 1)
        boxplot_axis = figure.add_subplot(2, 2, 2)
        heatmap_axis = figure.add_subplot(2, 2, 3)
        histogram_axis = figure.add_subplot(2, 2, 4)
        line_chart_data = draw_line_chart(self.df, line_chart_axis, include_anomalies=True)
        unique_timestamps = line_chart_data[COLUMN_TIMESTAMP].unique()
        configure_line_chart_xticks(line_chart_axis, unique_timestamps)
        draw_boxplot(self.df, boxplot_axis)
        heatmap_data = draw_heatmap(self.df, heatmap_axis)
        heatmap_timestamps = heatmap_data.columns.tolist()
        configure_heatmap_xticks(heatmap_axis, heatmap_timestamps)
        draw_histogram(self.df, histogram_axis)
        viz_tab.canvas.draw_idle()

    # View updates helpers

    def sync_sort_indicator(self, table, display_df):
        """Set the table header sort-indicator arrow to reflect the current sort state."""
        if self.table_sort_column in display_df.columns:
            sort_column_index = display_df.columns.get_loc(self.table_sort_column)
            sort_order = Qt.SortOrder.AscendingOrder if self.table_sort_ascending else Qt.SortOrder.DescendingOrder
            table.horizontalHeader().setSortIndicator(sort_column_index, sort_order)


if __name__ == "__main__":
    app = QApplication([])
    window = TemperatureAnalysisDashboard()
    window.showMaximized()
    app.exec()

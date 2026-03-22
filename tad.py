"""TAD – Temperature Analysis Dashboard: load, filter and visualize temperature sensor data."""

import pandas as pd
import requests
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from constants import (
    COLUMN_SENSOR_ID,
    COLUMN_TEMPERATURE,
    COLUMN_TIMESTAMP,
    DATETIME_FORMAT_PY,
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
    STATUS_FILE_LOAD_FAILED_TEMPLATE,
    STATUS_FILE_SAVE_FAILED_TEMPLATE,
    STATUS_LOAD_TEMPLATE,
    STATUS_NETWORK_LOAD_FAILED_TEMPLATE,
    STATUS_READY_MESSAGE,
    STATUS_SAVE_PDF_TEMPLATE,
    STATUS_SAVE_ROWS_TEMPLATE,
    STATISTICS_COLUMNS,
    VISUALIZATIONS_GRID_COLS,
    VISUALIZATIONS_GRID_ROWS,
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
    configure_chart_xticks,
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


class TemperatureAnalysisDashboard(QMainWindow):
    """Main application window orchestrating data loading, filtering and display."""

    # Setup

    def __init__(self):
        """Initialize state variables and assemble the central widget layout."""
        super().__init__()
        # State variables
        self.df = pd.DataFrame()
        self.original_df = pd.DataFrame()
        self.sensor_checkboxes = {}
        self.table_sort_ascending = True
        self.table_sort_column = None
        # UI setup
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        banner = Banner()
        main_layout.addWidget(banner)
        load_save_section = LoadSaveSection(self.open_file, self.open_network_file, self.save_file)
        main_layout.addWidget(load_save_section)
        self.filters_frame = FiltersFrame(self.apply_filters, self.reset_datetime_filters)
        main_layout.addWidget(self.filters_frame)
        self.results_tabs = ResultsTabs(self.on_table_header_clicked)
        main_layout.addWidget(self.results_tabs)
        self.setCentralWidget(main_widget)
        self.setWindowTitle(WINDOW_TITLE)
        self.statusBar().showMessage(STATUS_READY_MESSAGE)

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
        try:
            if file_path.lower().endswith(FILE_EXT_CSV):
                self.original_df = load_dataframe_from_csv(file_path)
            elif file_path.lower().endswith(FILE_EXT_JSON):
                self.original_df = load_dataframe_from_json(file_path)
            else:
                return
            self.process_loaded_data(file_path)
        except (KeyError, OSError, ValueError) as error:
            self.statusBar().showMessage(STATUS_FILE_LOAD_FAILED_TEMPLATE.format(error=error))

    def open_network_file(self):
        """Prompt the user for a URL, download the data, and load it into the dashboard."""
        default_url = NETWORK_DIALOG_DEFAULT_DATA_URL
        url, ok = QInputDialog.getText(self, NETWORK_DIALOG_TITLE, NETWORK_DIALOG_PROMPT, text=default_url)
        if not ok or not url.strip():
            return
        url = url.strip()
        try:
            self.original_df = load_dataframe_from_url(url)
        except requests.RequestException as error:
            self.statusBar().showMessage(STATUS_NETWORK_LOAD_FAILED_TEMPLATE.format(error=error))
            return
        try:
            self.process_loaded_data(url)
        except (KeyError, ValueError) as error:
            self.statusBar().showMessage(STATUS_FILE_LOAD_FAILED_TEMPLATE.format(error=error))

    def save_file(self):
        """Open a save dialog and export the filtered data to CSV, JSON or PDF."""
        if self.df.empty:
            QMessageBox.warning(self, "No data to save", "Load and filter data before saving.")
            return
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            FILE_DIALOG_SAVE_DATA_FILE_TITLE,
            "",
            FILE_DIALOG_SAVE_DATA_FILE_FILTER,
        )
        if not file_path:
            return
        try:
            file_path, saved_format = save_dataframe(self.df, file_path, selected_filter)
        except (IOError, OSError, ValueError) as error:
            self.statusBar().showMessage(STATUS_FILE_SAVE_FAILED_TEMPLATE.format(error=error))
            return
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
            self.table_sort_ascending = True
            self.table_sort_column = clicked_column
        self.update_data_table()

    # UI action helpers

    def process_loaded_data(self, data_source):
        """Normalize columns, rebuild filters, apply them, and update the status bar."""
        self.original_df = normalize_loaded_data(self.original_df)
        self.refresh_datetime_filters()
        self.refresh_sensor_filters()
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
        self.update_statistics()
        self.update_visualizations()

    def refresh_datetime_filters(self):
        """Show or hide date/time picker controls and set their bounds from the loaded data."""
        dt_filter = self.filters_frame.datetime_range_filter
        if self.original_df.empty:
            dt_filter.setVisible(False)
            return
        dt_filter.setVisible(True)
        min_timestamp = self.original_df[COLUMN_TIMESTAMP].min()
        min_qdatetime = dt_filter.from_edit.dateTimeFromText(min_timestamp.strftime(DATETIME_FORMAT_PY))
        max_timestamp = self.original_df[COLUMN_TIMESTAMP].max()
        max_qdatetime = dt_filter.to_edit.dateTimeFromText(max_timestamp.strftime(DATETIME_FORMAT_PY))
        set_datetime_filter_bounds(dt_filter, min_qdatetime, max_qdatetime)

    def refresh_sensor_filters(self):
        """Rebuild the sensor checkbox list from unique sensor IDs in the loaded data."""
        clear_layout(self.filters_frame.sensor_filter.values_layout)
        self.sensor_checkboxes = {}
        if self.original_df.empty:
            return
        self.filters_frame.setVisible(True)
        self.filters_frame.sensor_filter.setVisible(True)
        for sensor_id in sorted(self.original_df[COLUMN_SENSOR_ID].dropna().unique(), key=str):
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
            from_datetime = dt_filter.from_edit.dateTime().toPyDateTime()
            to_datetime = dt_filter.to_edit.dateTime().toPyDateTime()
            from_timestamp = pd.Timestamp(from_datetime)
            to_timestamp = pd.Timestamp(to_datetime)
            self.df = self.df[
                (self.df[COLUMN_TIMESTAMP] >= from_timestamp) & (self.df[COLUMN_TIMESTAMP] <= to_timestamp)
            ]

    # View updates

    def update_data_table(self):
        """Populate the table widget with rows from the filtered `DataFrame`."""
        data_tab = self.results_tabs.data_tab
        if self.df.empty:
            if self.original_df.empty:
                data_tab.label.setText(MESSAGE_INITIAL_DATA)
            else:
                data_tab.label.setText(MESSAGE_NO_DATA_FOR_FILTERS)
            data_tab.label.setVisible(True)
            data_tab.table.setVisible(False)
            return
        display_df = self.df
        if self.table_sort_column in self.df.columns:
            display_df = self.df.sort_values(self.table_sort_column, ascending=self.table_sort_ascending)
        else:
            self.table_sort_column = None
        data_tab.label.setVisible(False)
        data_tab.table.setColumnCount(len(display_df.columns))
        data_tab.table.setHorizontalHeaderLabels([str(column) for column in display_df.columns])
        data_tab.table.setRowCount(len(display_df))
        data_tab.table.setVisible(True)
        self.sync_sort_indicator(data_tab.table, display_df)
        for row_index, row_tuple in enumerate(display_df.itertuples(index=False)):
            for column_index, value in enumerate(row_tuple):
                data_tab.table.setItem(row_index, column_index, QTableWidgetItem(str(value)))

    def update_statistics(self):
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
        visualizations_tab = self.results_tabs.visualizations_tab
        if self.df.empty:
            visualizations_tab.label.setVisible(True)
            if self.original_df.empty:
                visualizations_tab.label.setText(MESSAGE_INITIAL_DATA)
            else:
                visualizations_tab.label.setText(MESSAGE_NO_DATA_FOR_FILTERS)
            visualizations_tab.canvas.setVisible(False)
            return
        visualizations_tab.canvas.setVisible(True)
        visualizations_tab.label.setVisible(False)
        figure = visualizations_tab.canvas.figure
        figure.clear()
        line_chart_axis = figure.add_subplot(VISUALIZATIONS_GRID_ROWS, VISUALIZATIONS_GRID_COLS, 1)
        boxplot_axis = figure.add_subplot(VISUALIZATIONS_GRID_ROWS, VISUALIZATIONS_GRID_COLS, 2)
        heatmap_axis = figure.add_subplot(VISUALIZATIONS_GRID_ROWS, VISUALIZATIONS_GRID_COLS, 3)
        histogram_axis = figure.add_subplot(VISUALIZATIONS_GRID_ROWS, VISUALIZATIONS_GRID_COLS, 4)
        line_chart_data = draw_line_chart(self.df, line_chart_axis)
        configure_chart_xticks(line_chart_axis, line_chart_data[COLUMN_TIMESTAMP].unique())
        draw_boxplot(self.df, boxplot_axis)
        heatmap_data = draw_heatmap(self.df, heatmap_axis)
        configure_chart_xticks(
            heatmap_axis, heatmap_data.columns.tolist(), tick_values=range(len(heatmap_data.columns))
        )
        draw_histogram(self.df, histogram_axis)
        visualizations_tab.canvas.draw_idle()

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

"""TAD – application-wide constants."""

# 1. Appearance

# 1.1. Window
WINDOW_TITLE = "TAD - Temperature Analysis Dashboard"

# 1.2. Banner
BANNER_FILE_PATH = "tad_banner.svg"
BANNER_HEIGHT = 100

# 1.3. Load/save panels

# 1.3.1. Load panel
LOAD_FROM_DISK_TEXT = "From disk"
LOAD_FROM_NETWORK_TEXT = "From network"
LOAD_GROUP_TITLE = "Load data"
SUPPORTED_LOAD_FORMATS_TEXT = "Supported formats: CSV, JSON"

# 1.3.2. Save panel
SAVE_AS_TEXT = "Save as"
SAVE_GROUP_TITLE = "Save data"
SUPPORTED_SAVE_FORMATS_TEXT = "Supported formats: CSV, JSON, PDF report"

# 1.4. Filters panel
FILTERS_DATETIME_RANGE_LABEL_TEXT = "Date/time range:"
FILTERS_GROUP_TITLE = "Filters"
FILTERS_FROM_LABEL_TEXT = "From:"
FILTERS_RESET_BUTTON_TEXT = "Reset date/time range"
FILTERS_SENSORS_LABEL_TEXT = "Sensors:"
FILTERS_SENSORS_SPACING = 8
FILTERS_TO_LABEL_TEXT = "To:"

# 1.5. Tabs

# 1.5.1. Data Tab
DATA_TAB_TITLE = "Data"

# 1.5.2. Statistics Tab
STATISTICS_TAB_TITLE = "Statistics"
STATISTICS_COLUMNS = 4
STATISTICS_HORIZONTAL_MARGIN = 16
STATISTICS_SPACING = 16

# 1.5.3. Visualizations Tab
VISUALIZATIONS_FIGURE_SIZE = (10, 4)
VISUALIZATIONS_TAB_TITLE = "Visualizations"

# 1.5.3.1. Line Chart
LINE_CHART_ANOMALY_LABEL_TEXT = "Anomaly"
LINE_CHART_ANOMALY_MARKER = "x"
LINE_CHART_ANOMALY_STD_MULTIPLIER = 2
LINE_CHART_LEGEND_LOCATION = "upper right"
LINE_CHART_TICK_LABEL_FORMAT = "%d %b\n%H:%M"
LINE_CHART_TITLE = "Temperature over time"
LINE_CHART_X_LABEL_TEXT = "Time"
LINE_CHART_X_LABEL_FONT_SIZE = 8
LINE_CHART_X_LABEL_ROTATION = 90
LINE_CHART_X_TICKS_COUNT = 16
LINE_CHART_Y_LABEL_TEXT = "Temperature"

# 1.5.3.2. Boxplot
BOXPLOT_TITLE = "Temperature boxplot by sensor"
BOXPLOT_X_LABEL_TEXT = "Sensor"
BOXPLOT_Y_LABEL_TEXT = "Temperature"

# 1.5.3.3. Heatmap
HEATMAP_ASPECT = "auto"
HEATMAP_CMAP = "coolwarm"
HEATMAP_TITLE = "Temperature heatmap"
HEATMAP_X_LABEL_TEXT = "Time"
HEATMAP_Y_LABEL_TEXT = "Sensor"

# 1.5.3.4. Histogram
HISTOGRAM_BIN_STEP = 0.5
HISTOGRAM_EDGE_COLOR = "white"
HISTOGRAM_TEMPERATURE_MULTIPLIER = 2
HISTOGRAM_TITLE = "Temperature histogram"
HISTOGRAM_X_LABEL_TEXT = "Temperature"
HISTOGRAM_Y_LABEL_TEXT = "Count"

# 1.5.4. Messages
MESSAGE_INITIAL_DATA = "Please load data to get started."
MESSAGE_NO_DATA_FOR_FILTERS = "No data for current filters."

# 1.6. Dialogs

# 1.6.1. File dialogs
FILE_DIALOG_OPEN_DATA_FILE_FILTER = "CSV files (*.csv);;JSON files (*.json)"
FILE_DIALOG_OPEN_DATA_FILE_TITLE = "Open data file"
FILE_DIALOG_SAVE_DATA_FILE_FILTER = "CSV files (*.csv);;JSON files (*.json);;PDF report (*.pdf)"
FILE_DIALOG_SAVE_DATA_FILE_TITLE = "Save data file"

# 1.6.2. Network dialog
NETWORK_DIALOG_DEFAULT_DATA_URL = "https://raw.githubusercontent.com/dorezler/tad/refs/heads/main/test_data.csv"
NETWORK_DIALOG_PROMPT = "Data URL:"
NETWORK_DIALOG_TITLE = "Load data from network"

# 1.7. Status bar
STATUS_LOAD_TEMPLATE = "Loaded {data_source} ({rows} rows)."
STATUS_NETWORK_LOAD_FAILED_TEMPLATE = "Failed to load data from network: {error}"
STATUS_READY_MESSAGE = MESSAGE_INITIAL_DATA
STATUS_SAVE_PDF_TEMPLATE = "Saved data to {file_path} (PDF)"
STATUS_SAVE_ROWS_TEMPLATE = "Saved data to {file_path} ({rows} rows)."

# 2. Data

# 2.1. Column names
COLUMN_SENSOR_ID = "sensor_id"
COLUMN_TEMPERATURE = "temperature"
COLUMN_TIMESTAMP = "timestamp"
COLUMN_NAMES = (COLUMN_TIMESTAMP, COLUMN_SENSOR_ID, COLUMN_TEMPERATURE)

# 2.2. Date/time formats
DATETIME_FORMAT_PY = "%Y-%m-%d %H:%M:%S"
DATETIME_FORMAT_QT = "yyyy-MM-dd HH:mm:ss"

# 3. File I/O

# 3.1. Extensions
FILE_EXT_CSV = ".csv"
FILE_EXT_JSON = ".json"
FILE_EXT_PDF = ".pdf"

# 3.2. Filters
FILE_DIALOG_SAVE_FILTER_TO_EXTENSION = {
    "CSV files (*.csv)": FILE_EXT_CSV,
    "JSON files (*.json)": FILE_EXT_JSON,
    "PDF report (*.pdf)": FILE_EXT_PDF,
}

# 3.3. Format
FORMAT_IN_MEMORY_IMAGE = "png"
FORMAT_JSON_DATE = "iso"
FORMAT_JSON_ORIENT = "records"

# 4. PDF report

# 4.1. Styles
PDF_CHART_SIZE = (8, 4)
PDF_STYLE_CODE = "Code"
PDF_STYLE_HEADING_2 = "Heading2"
PDF_STYLE_HEADING_3 = "Heading3"
PDF_STYLE_ITALIC = "Italic"
PDF_STYLE_NORMAL = "Normal"
PDF_STYLE_TITLE = "Title"

# 4.2. Content
PDF_FIGURE_CAPTION_TEMPLATE = "Fig. {index}. {caption}."
PDF_FILTERED_RANGE_TEMPLATE = "Filtered data range: {min_date} - {max_date}"
PDF_FOOTER_MESSAGE = "Report generated automatically by TAD."
PDF_GLOBAL_STATS_TITLE = "Global statistics (all filtered sensors)"
PDF_NO_DATA_MESSAGE = "No data to display."
PDF_REPORT_TITLE = "TAD Data Export"
PDF_SENSOR_TITLE_TEMPLATE = "Sensor {sensor_id}"
PDF_STATISTICS_SECTION_TITLE = "Statistics"
PDF_VISUALIZATIONS_TITLE = "Visualizations"

"""TAD – reusable Qt widget classes and helpers."""

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDateTimeEdit,
    QGridLayout,
    QGroupBox,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from constants import (
    BANNER_FILE_PATH,
    BANNER_HEIGHT,
    DATA_TAB_TITLE,
    FILTERS_DATETIME_RANGE_LABEL_TEXT,
    FILTERS_FROM_LABEL_TEXT,
    FILTERS_GROUP_TITLE,
    FILTERS_RESET_BUTTON_TEXT,
    FILTERS_SENSORS_LABEL_TEXT,
    FILTERS_SENSORS_SPACING,
    FILTERS_TO_LABEL_TEXT,
    MESSAGE_INITIAL_DATA,
    LOAD_FROM_DISK_TEXT,
    LOAD_FROM_NETWORK_TEXT,
    LOAD_GROUP_TITLE,
    DATETIME_FORMAT_QT,
    SAVE_AS_TEXT,
    SAVE_GROUP_TITLE,
    STATISTICS_TAB_TITLE,
    STATISTICS_COLUMNS,
    STATISTICS_HORIZONTAL_MARGIN,
    STATISTICS_SPACING,
    SUPPORTED_LOAD_FORMATS_TEXT,
    SUPPORTED_SAVE_FORMATS_TEXT,
    VISUALIZATIONS_FIGURE_SIZE,
    VISUALIZATIONS_TAB_TITLE,
)


class Banner(QWidget):
    """SVG banner widget displayed at the top of the main window."""

    def __init__(self):
        """Set up the fixed-height SVG widget inside a vertical layout."""
        super().__init__()
        layout = QVBoxLayout(self)
        banner_widget = QSvgWidget(BANNER_FILE_PATH)
        banner_widget.setFixedHeight(BANNER_HEIGHT)
        layout.addWidget(banner_widget)


class ChartsCanvas(FigureCanvasQTAgg):
    """Matplotlib figure canvas pre-configured for embedding in a Qt layout."""

    def __init__(self):
        """Initialize the `Figure` with a preset size, then pass it to the base class."""
        self.figure = Figure(figsize=VISUALIZATIONS_FIGURE_SIZE, tight_layout=True)
        super().__init__(self.figure)


class DataTableTab(QWidget):
    """Tab widget that renders loaded data as a sortable, read-only table."""

    def __init__(self, on_table_header_clicked):
        """Build the placeholder label and the initially hidden table widget."""
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel(MESSAGE_INITIAL_DATA)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSortIndicatorShown(True)
        self.table.horizontalHeader().sectionClicked.connect(on_table_header_clicked)
        self.table.setVisible(False)
        layout.addWidget(self.table)


class DateTimeRangeFilter(QWidget):
    """Filter widget allowing the user to narrow data by a date/time range."""

    def __init__(self, apply_filters_callback, reset_datetime_callback):
        """Create From/To date-time pickers and a Reset button, all initially hidden."""
        super().__init__()
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(FILTERS_DATETIME_RANGE_LABEL_TEXT))
        self.from_label = QLabel(FILTERS_FROM_LABEL_TEXT)
        self.from_label.setVisible(False)
        layout.addWidget(self.from_label)
        self.from_edit = QDateTimeEdit()
        self.from_edit.setDisplayFormat(DATETIME_FORMAT_QT)
        self.from_edit.setCalendarPopup(True)
        self.from_edit.setVisible(False)
        self.from_edit.dateTimeChanged.connect(apply_filters_callback)
        layout.addWidget(self.from_edit)
        self.to_label = QLabel(FILTERS_TO_LABEL_TEXT)
        self.to_label.setVisible(False)
        layout.addWidget(self.to_label)
        self.to_edit = QDateTimeEdit()
        self.to_edit.setDisplayFormat(DATETIME_FORMAT_QT)
        self.to_edit.setCalendarPopup(True)
        self.to_edit.setVisible(False)
        self.to_edit.dateTimeChanged.connect(apply_filters_callback)
        layout.addWidget(self.to_edit)
        self.reset_button = QPushButton(FILTERS_RESET_BUTTON_TEXT)
        self.reset_button.setVisible(False)
        self.reset_button.clicked.connect(reset_datetime_callback)
        layout.addWidget(self.reset_button)
        self.setVisible(False)


class FiltersFrame(QGroupBox):
    """Horizontal bar combining sensor checkboxes and date/time range controls."""

    def __init__(self, apply_filters_callback, reset_datetime_callback):
        """Compose a `SensorFilter` and a `DateTimeRangeFilter` side by side."""
        super().__init__(FILTERS_GROUP_TITLE)
        layout = QHBoxLayout(self)
        self.sensor_filter = SensorFilter()
        layout.addWidget(self.sensor_filter)
        self.datetime_range_filter = DateTimeRangeFilter(apply_filters_callback, reset_datetime_callback)
        layout.addWidget(self.datetime_range_filter)
        layout.addStretch()
        self.setVisible(False)


class LoadSaveSection(QWidget):
    """Toolbar row containing load and save group boxes."""

    def __init__(self, open_file_callback, open_network_callback, save_file_callback):
        """Arrange a `LoadSection` and a `SaveSection` horizontally."""
        super().__init__()
        layout = QHBoxLayout(self)
        self.load_section = LoadSection(open_file_callback, open_network_callback)
        layout.addWidget(self.load_section)
        self.save_section = SaveSection(save_file_callback)
        layout.addWidget(self.save_section)


class LoadSection(QGroupBox):
    """Group box with buttons to load data from disk or a network URL."""

    def __init__(self, open_file_callback, open_network_callback):
        """Create the 'From disk' and 'From network' buttons plus a format hint label."""
        super().__init__(LOAD_GROUP_TITLE)
        layout = QHBoxLayout(self)
        load_from_disk_button = QPushButton(LOAD_FROM_DISK_TEXT)
        load_from_disk_button.clicked.connect(open_file_callback)
        layout.addWidget(load_from_disk_button)
        load_from_network_button = QPushButton(LOAD_FROM_NETWORK_TEXT)
        load_from_network_button.clicked.connect(open_network_callback)
        layout.addWidget(load_from_network_button)
        layout.addWidget(QLabel(SUPPORTED_LOAD_FORMATS_TEXT))
        layout.addStretch()


class ResultsTabs(QTabWidget):
    """QTabWidget hosting the Data, Statistics and Visualizations tabs."""

    def __init__(self, on_table_header_clicked):
        """Instantiate and register the three result tab widgets."""
        super().__init__()
        self.data_tab = DataTableTab(on_table_header_clicked)
        self.addTab(self.data_tab, DATA_TAB_TITLE)
        self.stats_tab = StatisticsTab()
        self.addTab(self.stats_tab, STATISTICS_TAB_TITLE)
        self.viz_tab = VisualizationsTab()
        self.addTab(self.viz_tab, VISUALIZATIONS_TAB_TITLE)


class SaveSection(QGroupBox):
    """Group box with a 'Save as' button for exporting filtered data."""

    def __init__(self, save_file_callback):
        """Create the 'Save as' button and a supported-formats hint label."""
        super().__init__(SAVE_GROUP_TITLE)
        layout = QHBoxLayout(self)
        save_as_button = QPushButton(SAVE_AS_TEXT)
        save_as_button.clicked.connect(save_file_callback)
        layout.addWidget(save_as_button)
        layout.addWidget(QLabel(SUPPORTED_SAVE_FORMATS_TEXT))
        layout.addStretch()


class SensorFilter(QWidget):
    """Filter widget displaying a dynamic row of per-sensor toggle checkboxes."""

    def __init__(self):
        """Create an empty horizontal checkbox container, initially hidden."""
        super().__init__()
        layout = QHBoxLayout(self)
        layout.addWidget(QLabel(FILTERS_SENSORS_LABEL_TEXT))
        self.values_widget = QWidget()
        self.values_layout = QHBoxLayout(self.values_widget)
        self.values_layout.setContentsMargins(0, 0, 0, 0)
        self.values_layout.setSpacing(FILTERS_SENSORS_SPACING)
        layout.addWidget(self.values_widget)
        self.setVisible(False)


class StatisticsTab(QWidget):
    """Tab widget presenting global and per-sensor temperature statistics."""

    def __init__(self):
        """Build the statistics scroll area with a four-column grid layout."""
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel(MESSAGE_INITIAL_DATA)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.frames_container = QWidget()
        self.frames_layout = QGridLayout(self.frames_container)
        self.frames_layout.setContentsMargins(STATISTICS_HORIZONTAL_MARGIN, 0, STATISTICS_HORIZONTAL_MARGIN, 0)
        self.frames_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.frames_layout.setHorizontalSpacing(STATISTICS_SPACING)
        self.frames_layout.setVerticalSpacing(STATISTICS_SPACING)
        for column_index in range(STATISTICS_COLUMNS):
            self.frames_layout.setColumnStretch(column_index, 1)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.frames_container)
        self.scroll_area.setVisible(False)
        layout.addWidget(self.scroll_area)


class VisualizationsTab(QWidget):
    """Tab widget containing the embedded Matplotlib chart canvas."""

    def __init__(self):
        """Build the placeholder label and the initially hidden canvas widget."""
        super().__init__()
        layout = QVBoxLayout(self)
        self.label = QLabel(MESSAGE_INITIAL_DATA)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)
        self.canvas = ChartsCanvas()
        self.canvas.setVisible(False)
        layout.addWidget(self.canvas)


def build_stats_box(title, series):
    """Create and return a selectable-text QGroupBox with statistics for `series`."""
    box = QGroupBox(title)
    layout = QVBoxLayout(box)
    label = QLabel(series.describe().to_string(float_format=lambda v: f"{v:.1f}"))
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    layout.addWidget(label)
    return box


def clear_layout(layout):
    """Remove and schedule for deletion all widgets inside `layout`."""
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.deleteLater()


def set_datetime_filter_bounds(dt_filter, min_qdatetime, max_qdatetime):
    """Configure picker min/max/current values while blocking signals to prevent re-filtering."""
    dt_filter.from_edit.blockSignals(True)
    dt_filter.to_edit.blockSignals(True)
    dt_filter.from_edit.setMinimumDateTime(min_qdatetime)
    dt_filter.from_edit.setMaximumDateTime(max_qdatetime)
    dt_filter.from_edit.setDateTime(min_qdatetime)
    dt_filter.to_label.setVisible(True)
    dt_filter.to_edit.setVisible(True)
    dt_filter.to_edit.setMinimumDateTime(min_qdatetime)
    dt_filter.to_edit.setMaximumDateTime(max_qdatetime)
    dt_filter.to_edit.setDateTime(max_qdatetime)
    dt_filter.from_label.setVisible(True)
    dt_filter.from_edit.setVisible(True)
    dt_filter.from_edit.blockSignals(False)
    dt_filter.to_edit.blockSignals(False)
    dt_filter.reset_button.setVisible(True)

"""TAD – chart drawing and visualization helpers."""

import io

import numpy as np
from matplotlib.figure import Figure

from constants import (
    BOXPLOT_TITLE,
    BOXPLOT_X_LABEL_TEXT,
    BOXPLOT_Y_LABEL_TEXT,
    COLUMN_SENSOR_ID,
    COLUMN_TEMPERATURE,
    COLUMN_TIMESTAMP,
    FORMAT_IN_MEMORY_IMAGE,
    HEATMAP_ASPECT,
    HEATMAP_CMAP,
    HEATMAP_TITLE,
    HEATMAP_X_LABEL_TEXT,
    HEATMAP_Y_LABEL_FONT_SIZE,
    HEATMAP_Y_LABEL_TEXT,
    HISTOGRAM_BIN_STEP,
    HISTOGRAM_EDGE_COLOR,
    HISTOGRAM_TEMPERATURE_MULTIPLIER,
    HISTOGRAM_TITLE,
    HISTOGRAM_X_LABEL_TEXT,
    HISTOGRAM_Y_LABEL_TEXT,
    LINE_CHART_ANOMALY_LABEL_TEXT,
    LINE_CHART_ANOMALY_MARKER,
    LINE_CHART_ANOMALY_STD_MULTIPLIER,
    LINE_CHART_LEGEND_LOCATION,
    LINE_CHART_TICK_LABEL_FORMAT,
    LINE_CHART_TITLE,
    LINE_CHART_X_LABEL_TEXT,
    LINE_CHART_X_LABEL_FONT_SIZE,
    LINE_CHART_X_LABEL_ROTATION,
    LINE_CHART_X_TICKS_COUNT,
    LINE_CHART_Y_LABEL_TEXT,
    PDF_CHART_SIZE,
)


def build_pdf_figures(df):
    """Create and return a list of `(caption, Figure)` tuples for PDF export."""
    figures = []
    fig = Figure(figsize=PDF_CHART_SIZE, tight_layout=True)
    ax = fig.add_subplot(1, 1, 1)
    line_chart_data = draw_line_chart(df, ax)
    configure_chart_xticks(ax, line_chart_data[COLUMN_TIMESTAMP].unique())
    figures.append((LINE_CHART_TITLE, fig))
    fig2 = Figure(figsize=PDF_CHART_SIZE, tight_layout=True)
    ax2 = fig2.add_subplot(1, 1, 1)
    draw_histogram(df, ax2)
    figures.append((HISTOGRAM_TITLE, fig2))
    fig3 = Figure(figsize=PDF_CHART_SIZE, tight_layout=True)
    ax3 = fig3.add_subplot(1, 1, 1)
    draw_boxplot(df, ax3)
    figures.append((BOXPLOT_TITLE, fig3))
    fig4 = Figure(figsize=PDF_CHART_SIZE, tight_layout=True)
    ax4 = fig4.add_subplot(1, 1, 1)
    heatmap_data = draw_heatmap(df, ax4)
    configure_chart_xticks(
        ax4,
        heatmap_data.columns.tolist(),
        tick_values=np.arange(len(heatmap_data.columns)),
    )
    figures.append((HEATMAP_TITLE, fig4))
    return figures


def configure_chart_xticks(axis, timestamps, tick_values=None):
    """Sub-sample `timestamps` and apply readable labels at positions from `tick_values` (or timestamps)."""
    if tick_values is None:
        tick_values = timestamps
    configure_xticks_with_formatted_labels(axis, timestamps, tick_values)


def configure_xticks_with_formatted_labels(axis, timestamps, tick_values):
    """Configure x-axis ticks and labels with formatted timestamps from `timestamps` applied to `tick_values`."""
    tick_values = np.asarray(tick_values)
    x_tick_indices = np.linspace(0, len(timestamps) - 1, LINE_CHART_X_TICKS_COUNT).astype(int)
    x_tick_labels = [timestamps[i].strftime(LINE_CHART_TICK_LABEL_FORMAT) for i in x_tick_indices]
    axis.set_xticks(tick_values[x_tick_indices])
    axis.set_xticklabels(
        x_tick_labels,
        rotation=LINE_CHART_X_LABEL_ROTATION,
        fontsize=LINE_CHART_X_LABEL_FONT_SIZE,
    )


def draw_boxplot(df, axis):
    """Draw a per-sensor temperature boxplot on `axis`."""
    grouped = [sensor_data[COLUMN_TEMPERATURE] for _, sensor_data in df.groupby(COLUMN_SENSOR_ID)]
    labels = [str(sensor_id) for sensor_id in df[COLUMN_SENSOR_ID].unique()]
    axis.boxplot(grouped, tick_labels=labels)
    axis.set_title(BOXPLOT_TITLE)
    axis.set_xlabel(BOXPLOT_X_LABEL_TEXT)
    axis.set_ylabel(BOXPLOT_Y_LABEL_TEXT)


def draw_heatmap(df, axis):
    """Draw a sensor × time temperature heatmap on `axis`."""
    heatmap_data = df.pivot(index=COLUMN_SENSOR_ID, columns=COLUMN_TIMESTAMP, values=COLUMN_TEMPERATURE)
    image = axis.imshow(heatmap_data, aspect=HEATMAP_ASPECT, cmap=HEATMAP_CMAP)
    axis.set_title(HEATMAP_TITLE)
    axis.set_xlabel(HEATMAP_X_LABEL_TEXT)
    axis.set_ylabel(HEATMAP_Y_LABEL_TEXT)
    axis.figure.colorbar(image, ax=axis)
    axis.set_yticks(np.arange(len(heatmap_data.index)))
    axis.set_yticklabels([str(idx) for idx in heatmap_data.index], fontsize=HEATMAP_Y_LABEL_FONT_SIZE)
    return heatmap_data


def draw_histogram(df, axis):
    """Draw a half-degree-bin temperature frequency histogram on `axis`."""
    temperature_values = df[COLUMN_TEMPERATURE].dropna()
    min_temperature, max_temperature, bin_edges = histogram_bin_edges(temperature_values)
    axis.hist(temperature_values, bins=bin_edges, edgecolor=HISTOGRAM_EDGE_COLOR)
    tick_start = np.floor(min_temperature)
    tick_end = np.ceil(max_temperature)
    axis.set_xticks(np.arange(tick_start, tick_end + 1, 1))
    axis.set_title(HISTOGRAM_TITLE)
    axis.set_xlabel(HISTOGRAM_X_LABEL_TEXT)
    axis.set_ylabel(HISTOGRAM_Y_LABEL_TEXT)


def draw_line_chart(df, axis):
    """Draw temperature time-series per sensor and mark statistical anomalies."""
    line_chart_data = df.sort_values(COLUMN_TIMESTAMP)
    anomaly_label_added = False
    for sensor_id, sensor_data in line_chart_data.groupby(COLUMN_SENSOR_ID):
        axis.plot(
            sensor_data[COLUMN_TIMESTAMP],
            sensor_data[COLUMN_TEMPERATURE],
            label=str(sensor_id),
        )
        sensor_std = sensor_data[COLUMN_TEMPERATURE].std()
        sensor_mean = sensor_data[COLUMN_TEMPERATURE].mean()
        # Flag readings more than `LINE_CHART_ANOMALY_STD_MULTIPLIER` × standard deviation from the per-sensor mean.
        anomalies = sensor_data[
            (sensor_data[COLUMN_TEMPERATURE] - sensor_mean).abs() > (LINE_CHART_ANOMALY_STD_MULTIPLIER * sensor_std)
        ]
        if not anomalies.empty:
            axis.scatter(
                anomalies[COLUMN_TIMESTAMP],
                anomalies[COLUMN_TEMPERATURE],
                marker=LINE_CHART_ANOMALY_MARKER,
                label=LINE_CHART_ANOMALY_LABEL_TEXT if not anomaly_label_added else None,
            )
            anomaly_label_added = True
    axis.set_title(LINE_CHART_TITLE)
    axis.set_xlabel(LINE_CHART_X_LABEL_TEXT)
    axis.set_ylabel(LINE_CHART_Y_LABEL_TEXT)
    legend_handles, legend_labels = axis.get_legend_handles_labels()
    legend_handles, legend_labels = move_anomaly_to_legend_end(legend_handles, legend_labels)
    axis.legend(legend_handles, legend_labels, loc=LINE_CHART_LEGEND_LOCATION)
    return line_chart_data


def fig_to_png_buffer(fig):
    """Render `fig` to an in-memory PNG buffer and return it seeked to the start."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format=FORMAT_IN_MEMORY_IMAGE)
    buffer.seek(0)
    return buffer


def histogram_bin_edges(temperature_values):
    """Return `(min_t, max_t, bin_edges)` rounded outward to the nearest `HISTOGRAM_BIN_STEP` step in °C."""
    min_temperature = (
        np.floor(temperature_values.min() * HISTOGRAM_TEMPERATURE_MULTIPLIER) / HISTOGRAM_TEMPERATURE_MULTIPLIER
    )
    max_temperature = (
        np.ceil(temperature_values.max() * HISTOGRAM_TEMPERATURE_MULTIPLIER) / HISTOGRAM_TEMPERATURE_MULTIPLIER
    )
    edges = np.arange(min_temperature, max_temperature + HISTOGRAM_BIN_STEP, HISTOGRAM_BIN_STEP)
    if len(edges) < 2:
        edges = np.array([min_temperature, min_temperature + HISTOGRAM_BIN_STEP])
    return min_temperature, max_temperature, edges


def move_anomaly_to_legend_end(handles, labels):
    """Move the Anomaly entry to the end of `handles`/`labels` and return both lists."""
    if LINE_CHART_ANOMALY_LABEL_TEXT in labels:
        anomaly_index = labels.index(LINE_CHART_ANOMALY_LABEL_TEXT)
        anomaly_handle = handles.pop(anomaly_index)
        labels.pop(anomaly_index)
        handles.append(anomaly_handle)
        labels.append(LINE_CHART_ANOMALY_LABEL_TEXT)
    return handles, labels

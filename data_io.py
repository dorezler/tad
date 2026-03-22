"""TAD – data loading, normalization and saving helpers."""

import io
import json

import pandas as pd
import requests

from constants import (
    COLUMN_NAMES,
    COLUMN_TIMESTAMP,
    FILE_DIALOG_SAVE_FILTER_TO_EXTENSION,
    FILE_EXT_CSV,
    FILE_EXT_JSON,
    FILE_EXT_PDF,
    FORMAT_JSON_DATE,
    FORMAT_JSON_INDENT,
    FORMAT_JSON_ORIENT,
    NETWORK_REQUEST_TIMEOUT,
)
from report import export_pdf_report


def ensure_extension(file_path, extension):
    """Return `file_path` suffixed with `extension` if it does not already end with it."""
    if not file_path.lower().endswith(extension):
        return f"{file_path}{extension}"
    return file_path


def load_dataframe_from_csv(csv_file_path):
    """Read a CSV file and return its contents as a `DataFrame`."""
    return pd.read_csv(csv_file_path)


def load_dataframe_from_json(json_file_path):
    """Read a JSON records file and return its contents as a `DataFrame`."""
    return pd.read_json(json_file_path, orient=FORMAT_JSON_ORIENT)


def load_dataframe_from_url(url, timeout=NETWORK_REQUEST_TIMEOUT):
    """Download tabular data from `url` and return it as a `DataFrame`."""
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    try:
        return pd.DataFrame.from_records(response.json())
    except json.JSONDecodeError:
        return pd.read_csv(io.StringIO(response.text))


def normalize_loaded_data(df):
    """Return a normalized copy of loaded data with required columns and parsed timestamps."""
    missing_columns = set(COLUMN_NAMES) - set(df.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing_columns))}")
    normalized_df = df[list(COLUMN_NAMES)].copy()
    normalized_df[COLUMN_TIMESTAMP] = pd.to_datetime(normalized_df[COLUMN_TIMESTAMP])
    return normalized_df


def save_dataframe(df, file_path, selected_filter):
    """Save `df` to CSV, JSON or PDF based on dialog filter and file extension."""
    file_path_lower = file_path.lower()
    if file_path_lower.endswith(FILE_EXT_CSV):
        target_extension = FILE_EXT_CSV
    elif file_path_lower.endswith(FILE_EXT_JSON):
        target_extension = FILE_EXT_JSON
    elif file_path_lower.endswith(FILE_EXT_PDF):
        target_extension = FILE_EXT_PDF
    else:
        target_extension = FILE_DIALOG_SAVE_FILTER_TO_EXTENSION.get(selected_filter, FILE_EXT_CSV)
    if target_extension == FILE_EXT_JSON:
        file_path = ensure_extension(file_path, FILE_EXT_JSON)
        df.to_json(file_path, date_format=FORMAT_JSON_DATE, indent=FORMAT_JSON_INDENT, orient=FORMAT_JSON_ORIENT)
        return file_path, FILE_EXT_JSON
    if target_extension == FILE_EXT_PDF:
        file_path = ensure_extension(file_path, FILE_EXT_PDF)
        export_pdf_report(df, file_path)
        return file_path, FILE_EXT_PDF
    file_path = ensure_extension(file_path, FILE_EXT_CSV)
    df.to_csv(file_path, index=False)
    return file_path, FILE_EXT_CSV

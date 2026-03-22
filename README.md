# TAD – Temperature Analysis Dashboard

A desktop application for loading, filtering, and visualizing temperature sensor data. Supports importing data from CSV/JSON files and network sources, with the ability to export reports to PDF.

## Features

- 📁 Load/save CSV/JSON files
- 🔗 Load data from network sources with automatic format detection
- 🛠️ Filtering/sorting:
  - ⚙️ Filter data by sensors and time ranges
  - ⚡ Live updates of table, statistics and charts on filter change
  - 🗂️ Sortable data table with ascending/descending column sort
- 📈 Statistical analysis of temperature data (per sensor and global)
- 📊 Interactive visualization of temperature data:
  - 📈 Line chart
    - 🚨 Anomaly detection in sensor readings
  - 📦 Box plot
  - 🌡️ Heatmap
  - 📊 Histogram
- 🖨️ Export reports to PDF

## Installation

### Requirements

- Python 3.14
- pip

### Install from source

```bash
git clone https://github.com/dorezler/tad.git
cd tad
pip install -r requirements.txt
```

### Run

```bash
python tad.py
```

## Dependencies

See [requirements.txt](requirements.txt) for a complete list of dependencies.

## Data Format

TAD expects data files with the following column structure:

| Column | Type | Description |
|--------|------|-------------|
| `timestamp` | DateTime | ISO 8601 formatted date/time |
| `sensor_id` | String | Unique sensor identifier |
| `temperature` | Float | Temperature value (°C) |

### CSV Example

```csv
timestamp,sensor_id,temperature
2026-03-22T08:00:00,SENSOR_01,4.5
2026-03-22T08:05:00,SENSOR_01,4.3
2026-03-22T08:00:00,SENSOR_02,3.8
```

### JSON Example

```json
[
  {"timestamp": "2026-03-22T08:00:00", "sensor_id": "SENSOR_01", "temperature": 4.5},
  {"timestamp": "2026-03-22T08:05:00", "sensor_id": "SENSOR_01", "temperature": 4.3},
  {"timestamp": "2026-03-22T08:00:00", "sensor_id": "SENSOR_02", "temperature": 3.8}
]
```

## License

MIT License – see [LICENSE](LICENSE) file.

## Author

Dorota Rezler

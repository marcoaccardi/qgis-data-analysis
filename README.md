# QGIS Sonification Pipeline

A comprehensive geospatial processing pipeline that extracts, analyzes, and prepares terrain data for sonification applications. This pipeline transforms Digital Elevation Models (DEMs) into various terrain features and formats suitable for both tabular and image-based sonification.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [Processing Stages](#processing-stages)
- [Output Files](#output-files)
- [Visualization](#visualization)
- [Troubleshooting](#troubleshooting)
- [Documentation](#documentation)

## Overview

The QGIS Sonification Pipeline is designed to process terrain data (Digital Elevation Models) into formats that can be used for sonification - the process of representing data through sound. The pipeline extracts multiple terrain features, creates zones based on terrain characteristics, calculates statistics, and generates time-series data along paths that can be directly used for audio synthesis.

## Features

- **Comprehensive Terrain Analysis**: Extract slope, aspect, curvature, roughness, TPI, TRI, and TWI (when SAGA is available)
- **Automatic Data Preparation**: Converts, reprojects, and normalizes DEM files
- **Zonal Masking**: Identifies and segments terrain zones based on characteristics
- **Vector Conversion**: Converts raster data to vector formats for path-based analysis
- **Time Series Generation**: Creates temporal sequences of terrain values along paths
- **Visualization**: Generates standard, relief, and hillshade visualizations of all data
- **Batch Processing**: Process multiple datasets sequentially with logging
- **SAGA Provider Support**: Gracefully handles missing SAGA provider for TWI calculation

## Requirements

- QGIS 3.x with Python 3 support
- GDAL/OGR libraries
- GRASS GIS modules (for certain terrain calculations)
- SAGA GIS (optional, for Topographic Wetness Index calculations)
- Python dependencies:
  - numpy
  - matplotlib
  - pandas

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/qgis_sonification_pipeline.git
   cd qgis_sonification_pipeline
   ```

2. Ensure QGIS and dependencies are installed:
   ```bash
   # Example for Ubuntu/Debian
   sudo apt-get install qgis python3-qgis saga grass
   ```

3. Prepare your data by placing ASC files in the `dataset` folder.

## Project Structure

```
qgis_sonification_pipeline/
├── dataset/                  # Source ASC/DEM files
├── output/                   # Generated outputs organized by dataset
├── scripts/                  # Core processing scripts
│   ├── 01_load_and_prepare_raster.py
│   ├── 02_compute_features.py
│   ├── 03_create_zonal_masks.py
│   ├── 04_zonal_statistics.py
│   ├── 05_vectorize_masks.py
│   └── 06_temporal_simulation.py
├── utils/                    # Utility modules and tools
│   ├── config_utils.py
│   ├── convert_asc_to_png.py
│   ├── qgis_utils.py
│   ├── raster_utils.py
│   ├── vector_utils.py
│   └── qgis_tools/          # QGIS diagnostic tools
├── visualizations/           # Generated PNG visualizations
├── logs/                     # Processing and visualization logs
├── run_sonification_pipeline.sh    # Main pipeline runner
├── run_all_datasets.sh             # Batch processing script
├── generate_all_visualizations.sh  # Batch visualization script
└── SONIFICATION_PIPELINE_DOCUMENTATION.md  # Detailed documentation
```

## Usage

### Process a Single Dataset

To process a single ASC file:

```bash
./run_sonification_pipeline.sh -i dataset/your_dem.asc -o output -v
```

Parameters:
- `-i`: Input ASC file path
- `-o`: Output directory (default: output)
- `-v`: Verbose mode (shows detailed output)

### Process All Datasets

To process all ASC files in the dataset folder and generate visualizations:

```bash
./run_all_datasets.sh
```

This will:
1. Process all ASC files in the dataset folder
2. Generate all terrain features and derivatives
3. Create visualizations for all outputs
4. Save logs to the logs folder

### Generate Visualizations Only

To only generate visualizations for already processed data:

```bash
./generate_all_visualizations.sh
```

## Processing Stages

The pipeline consists of six sequential stages:

1. **Input Preparation**: Load, reproject, and prepare input ASC/DEM files
2. **Feature Extraction**: Calculate terrain features (slope, aspect, curvature, etc.)
3. **Zonal Masks**: Create binary masks for terrain feature zones
4. **Zonal Statistics**: Calculate statistical metrics for each zone
5. **Vectorization**: Convert raster masks to vector format
6. **Temporal Simulation**: Generate time-series data along specified paths

## Output Files

The pipeline generates various output formats organized by dataset:

- **TIF Files**: GeoTIFF rasters of terrain features and masks
- **CSV Files**: Tabular data with time-series values and statistics
- **JSON Files**: Metadata and configuration information
- **GeoJSON Files**: Vector representations of terrain features
- **PNG Files**: Visualizations of all raster outputs

For sonification purposes, these are the most relevant outputs:

- `combined_time_series.csv`: All terrain features along a path (tabular sonification)
- `*_clean_csvready.tif`: NoData-adjusted rasters for image sonification
- Visualizations in the `visualizations` folder

## Visualization

The pipeline generates three types of visualizations for each raster file:

1. **Standard**: Basic visualization with default scaling
2. **Relief**: Color-relief visualization highlighting terrain variations
3. **Hillshade**: Shaded relief visualization showing terrain topography

These visualizations are saved in the `visualizations` folder, organized by dataset and feature name.

## Troubleshooting

### Common Issues

- **SAGA Provider Missing**: The pipeline will skip TWI calculation without error if SAGA is unavailable
- **Segmentation Faults**: Occasionally QGIS may report segmentation faults after processing completes, but this does not affect output quality
- **NoData Values**: The checkerboard pattern in visualizations (approximately 50% NoData) is expected for datasets with systematic data gaps

### Checking Available Algorithms

To check if specific algorithms are available:

```bash
python3 utils/qgis_tools/list_qgis_algorithms.py
```

## Documentation

For detailed explanations of data structures, file formats, and processing methods, refer to the [SONIFICATION_PIPELINE_DOCUMENTATION.md](SONIFICATION_PIPELINE_DOCUMENTATION.md) file.

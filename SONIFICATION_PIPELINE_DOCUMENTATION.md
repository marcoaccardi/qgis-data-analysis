# QGIS Sonification Pipeline Documentation

## Project Overview

The QGIS Sonification Pipeline is a comprehensive data processing framework designed to extract, analyze, and prepare geospatial terrain data for sonification. The pipeline transforms Digital Elevation Models (DEMs) into various terrain features, processes them for consistency, and extracts time-series data along predefined paths. The processed data is structured to be readily used in sonification applications, allowing for the auditory representation of terrain features.

## Data Flow

The pipeline follows a sequential processing workflow:

1. **Input**: ASC/DEM files (Digital Elevation Models)
2. **Processing**: Extraction of terrain features, creation of zonal masks, calculation of statistics
3. **Output**: Structured data in various formats (TIF, CSV, JSON, PNG) ready for sonification

## File Types and Data Formats

### ASC Files (Input)
- **Description**: ASCII Grid files containing elevation data
- **Structure**: Header with metadata followed by a grid of elevation values
- **Usage**: Source data representing the terrain elevation
- **Example**: `S0606-M3-Tempus_Fugit-UTM16N-1m.asc`

### TIF Files (Processed Data)
- **Description**: GeoTIFF raster files containing terrain feature data
- **Types**:
  - **Original Reprojected DEM**: `dataset_name.tif` - Converted ASC file
  - **Feature Files**: `feature_name.tif` - Extracted terrain features (slope, aspect, etc.)
  - **Clean Files**: `feature_name_clean.tif` - Feature files with preserved NoData values
  - **CSV-Ready Files**: `feature_name_clean_csvready.tif` - NoData replaced with zeros for CSV extraction
- **Location**: `output/dataset_name/features/` and `output/dataset_name/sonification_rasters/`
- **Usage**: Core analytical data for sonification

### PNG Files (Visualizations)
- **Description**: Visual representations of the TIF files
- **Types**:
  - **Standard**: Basic visualization with default scaling
  - **Relief**: Color-relief visualization highlighting terrain variations
  - **Hillshade**: Shaded relief visualization showing terrain topography
- **Location**: `visualizations/dataset_name/feature_name/`
- **Usage**: Visual validation and reference, potentially for image-based sonification

### CSV Files (Tabular Data)
- **Description**: Comma-separated values containing extracted terrain feature values
- **Types**:
  - **Combined Time Series**: `combined_time_series.csv` - All features along a path
  - **Path Points**: `path_points.csv` - Coordinates of points along the sonification path
  - **Zonal Statistics**: Various statistics files for different zones
- **Location**: Root of output folder and in time_series subfolder
- **Usage**: Primary data source for tabular-based sonification

### JSON Files (Metadata and Configuration)
- **Description**: JavaScript Object Notation files containing metadata and configuration
- **Types**:
  - **Feature List**: `feature_list.json` - Available terrain features
  - **Mask Metadata**: `mask_metadata.json` - Information about zonal masks
  - **Vector Metadata**: `vector_metadata.json` - Information about vector features
  - **Temporal Simulation Metadata**: `temporal_simulation_metadata.json` - Time series parameters
- **Location**: Root of output folder
- **Usage**: Provides context and parameters for sonification processing

### GeoJSON Files (Vector Data)
- **Description**: Geographic JSON files containing vector representations of terrain features
- **Location**: `output/dataset_name/geojson/`
- **Usage**: Vector representation of terrain features, potentially for path-based sonification

## Python Scripts

### 1. Data Preparation (`01_load_and_prepare_raster.py`)
- **Purpose**: Loads, reprojects, and prepares the input ASC files
- **Output**: Reprojected TIF files ready for feature extraction
- **Key Functions**: ASC to TIF conversion, coordinate system transformation

### 2. Feature Extraction (`02_compute_features.py`)
- **Purpose**: Calculates terrain features from the DEM
- **Features Generated**:
  - Slope
  - Aspect 
  - Curvature (Profile and Planform)
  - Roughness
  - TPI (Topographic Position Index)
  - TRI (Terrain Ruggedness Index)
  - TWI (Topographic Wetness Index) - if SAGA provider is available
- **Output**: TIF files for each terrain feature
- **Note**: Handles missing SAGA provider gracefully for TWI calculation

### 3. Zonal Masks Creation (`03_create_zonal_masks.py`)
- **Purpose**: Creates binary masks for identifying specific terrain zones
- **Process**: Applies thresholds to terrain features to identify zones of interest
- **Output**: Binary mask TIF files for each zone

### 4. Zonal Statistics (`04_zonal_statistics.py`)
- **Purpose**: Calculates statistical metrics for each zone
- **Metrics**: Min, max, mean, median, standard deviation, etc.
- **Output**: CSV files with zonal statistics

### 5. Mask Vectorization (`05_vectorize_masks.py`)
- **Purpose**: Converts raster masks to vector format
- **Process**: Polygonization of zonal masks
- **Output**: Shapefile and GeoJSON vector representations

### 6. Temporal Simulation (`06_temporal_simulation.py`)
- **Purpose**: Generates time-series data for sonification
- **Process**: Extracts terrain feature values along defined paths
- **Output**: CSV files with feature values at regular intervals along paths

## Visualization Script (`convert_asc_to_png.py`)
- **Purpose**: Generates visualizations from TIF files
- **Options**: Standard, relief, and hillshade visualizations
- **Output**: PNG images organized by dataset and feature type

## Data Characteristics and Patterns

### Checkerboard Pattern
- **Description**: Systematic data gaps creating a checkerboard appearance
- **Cause**: Intentional pattern in the original dataset or a result of the extraction process
- **Significance**: 
  - Approximately 50% of data is valid (as shown in gdalinfo statistics)
  - NoData values (-9999) are preserved through the pipeline
- **Handling**: 
  - Clean files preserve NoData values
  - CSV-ready files replace NoData with zeros only where needed for tabular export

## Recommended Data for Sonification

### For Tabular-Based Sonification
1. **Primary Dataset**: `combined_time_series.csv`
   - Contains all terrain features along the path
   - Already filtered to include only valid data points
   - Structured for temporal sonification

2. **Alternative Datasets**:
   - `path_points.csv` for spatial reference
   - Zonal statistics files for feature-based sonification

### For Image-Based Sonification
1. **Primary Files**: `*_clean_csvready.tif` or their PNG representations
   - Consistent handling of NoData values (replaced with zeros)
   - Complete spatial coverage for consistent sonification

2. **Alternative Files**:
   - Relief or hillshade visualizations for enhanced terrain representation
   - Original feature TIF files for raw data sonification (with NoData handling)

## Additional Notes

1. **Data Integrity**: The pipeline maintains the spatial integrity of the original data, preserving patterns and NoData values where appropriate.

2. **SAGA Provider Issue**: The pipeline gracefully handles missing SAGA provider by skipping TWI calculation without showing error messages.

3. **Segmentation Faults**: Occasional segmentation faults occur after script completion but do not affect output quality or correctness.

4. **Missing Values Strategy**: The pipeline employs a consistent approach to missing values:
   - Preserves NoData in analytical outputs
   - Replaces NoData with zeros only for CSV extraction
   - Maintains the original data distribution pattern

## Conclusion

This sonification pipeline provides a comprehensive framework for converting terrain data into formats suitable for sonification. Whether using tabular data for temporal sonification or images for spatial sonification, the processed outputs maintain data integrity while providing flexible options for different sonification approaches.

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

## Output and Visualizations Directory File Types

This section provides a detailed description of the file types and their purposes found in the `output` and `visualizations` directories of the QGIS Sonification Pipeline. This will help you understand what each file represents and how it is used in your workflow.

## 1. Output Directory
Each subdirectory in `output/` corresponds to a specific project or area. Inside each, you will find the following types of files and folders:

### Raster Data Files
- `.tif` : GeoTIFF raster files, typically representing elevation data (DEM) or derived spatial features (e.g., slope, aspect, roughness).
- `.tif.aux.xml` : Auxiliary metadata for the corresponding `.tif` file, used by GIS software.

### Vector Data Files
- `.shp`, `.shx`, `.dbf`, `.prj` : Shapefile components for vector data such as masks (e.g., ridges, valleys, erosion risk zones). These files work together to define the geometry and attributes of spatial features.
- `.cpg` : Specifies character encoding for shapefile attribute data.
- `.geojson` : GeoJSON vector files representing spatial masks or features in a widely used web-friendly format.

### Feature and Mask Data
- `features/` : Contains derived raster features (e.g., aspect, slope, curvature) as `.tif` files.
- `masks/` : Contains binary raster masks for specific zones (e.g., ridge, valley, erosion risk) as `.tif` files.
- `sonification_masks/` : Cleaned and CSV-ready binary raster masks for sonification, as `.tif` files.
- `sonification_rasters/` : Cleaned and CSV-ready derived raster features for sonification, as `.tif` files and corresponding CSVs.

### Statistical and Time Series Data
- `all_zones_statistics.csv` : Summary statistics for all zones.
- `combined_time_series.csv` : Aggregated time series data for all features/zones.
- `time_series/` : Contains per-feature time series CSVs (e.g., `slope_time_series.csv`).
- `stats/` : Contains per-feature statistics in both CSV and JSON formats (e.g., `slope_stats.csv`, `slope_stats.json`).
- `statistics/` : May contain further breakdowns by zone (e.g., `erosion_risk/`, `ridge/`, `valley/`).

### Metadata
- `feature_list.json` : List and descriptions of derived features.
- `mask_metadata.json` : Metadata about mask generation and properties.
- `temporal_simulation_metadata.json` : Details about temporal simulation parameters and results.
- `vector_metadata.json` : Metadata about vector data sources and attributes.
- `zonal_statistics_metadata.json` : Metadata about zonal statistics calculations.

### Other
- `path_points.csv` : CSV containing the coordinates and order of path points, likely for sonification or analysis.

## 2. Visualizations Directory
Each subdirectory or file in `visualizations/` corresponds to a specific project/area. Inside, you will find:

### Visualization Images
- `_hillshade.png` : Hillshade visualization of the DEM, enhancing terrain relief for visual interpretation.
- `_relief.png` : Colored relief map, often combining elevation and slope for visual effect.
- `_standard.png` : Standard visualization of the DEM or feature raster, typically using a color ramp.
- `.aux.xml` : Auxiliary metadata for the corresponding PNG file.

### Directory Structure
- Each visualization type (hillshade, relief, standard) is stored as a PNG image inside a subdirectory named after the project/area.

---

## Feature Descriptions

The following features are derived from the terrain data and are used throughout the pipeline for analysis and sonification:

- **Slope**: The steepness or degree of incline of the terrain, typically measured in degrees or percent. Indicates how rapidly elevation changes over a given distance.
- **Aspect**: The compass direction that a slope faces, measured in degrees from north. Useful for analyzing sunlight exposure, wind direction, and ecological patterns.
- **Roughness**: A measure of the variability in elevation within a local neighborhood, reflecting the ruggedness or smoothness of the terrain.
- **TPI (Topographic Position Index)**: The difference between a cell’s elevation and the average elevation of its surrounding neighborhood. Used to classify landscape positions such as ridges, valleys, and flats.
- **TRI (Terrain Ruggedness Index)**: Quantifies the total elevation change between a cell and its neighbors, providing a measure of terrain heterogeneity.
- **Curvature**: The rate of change of slope, indicating whether a surface is convex (e.g., ridge) or concave (e.g., valley). Useful for hydrological and geomorphological analysis.
- **Planform Curvature**: The curvature of contour lines (perpendicular to the slope direction), describing the convergence or divergence of flow across the surface.

---

## Summary Table
| File/Folder                   | Type           | Purpose/Description                                                  |
|------------------------------|----------------|---------------------------------------------------------------------|
| *.tif                        | Raster         | Elevation or derived feature raster data (GeoTIFF)                  |
| *.tif.aux.xml                | Metadata       | Auxiliary metadata for raster files                                 |
| *.shp, *.shx, *.dbf, *.prj   | Vector         | Shapefile components for masks/zones                                |
| *.cpg                        | Metadata       | Encoding for shapefile attributes                                   |
| *.geojson                    | Vector         | GeoJSON format masks/zones                                          |
| features/                    | Folder         | Derived raster features (aspect, slope, etc.)                       |
| masks/                       | Folder         | Binary raster masks for spatial zones                               |
| sonification_masks/          | Folder         | Cleaned/CSV-ready masks for sonification                            |
| sonification_rasters/        | Folder         | Cleaned/CSV-ready features for sonification                         |
| all_zones_statistics.csv     | Table (CSV)    | Summary statistics for all zones                                    |
| combined_time_series.csv     | Table (CSV)    | Combined time series for all features/zones                         |
| time_series/                 | Folder         | Per-feature time series CSVs                                        |
| stats/                       | Folder         | Per-feature statistics (CSV/JSON)                                   |
| statistics/                  | Folder         | Per-zone statistics breakdown                                       |
| feature_list.json            | Metadata       | List and descriptions of features                                   |
| mask_metadata.json           | Metadata       | Metadata about masks                                                |
| temporal_simulation_metadata.json | Metadata   | Temporal simulation details                                         |
| vector_metadata.json         | Metadata       | Metadata about vector data                                          |
| zonal_statistics_metadata.json | Metadata      | Metadata about zonal statistics                                     |
| path_points.csv              | Table (CSV)    | Ordered path points for analysis/sonification                       |
| *_hillshade.png              | Image          | Hillshade visualization of DEM                                      |
| *_relief.png                 | Image          | Colored relief visualization                                        |
| *_standard.png               | Image          | Standard DEM/feature visualization                                  |
| *.aux.xml (PNG)              | Metadata       | Auxiliary metadata for visualization images                         |

---

## CSV Processing for Sonification

The pipeline now includes specialized scripts to process CSV data for synchronized sonification with image visualizations:

### 1. Column-wise Sorting (`reorder_csv_for_column_scan.py`)

This script re-orders the combined time series data to follow a column-by-column pattern:

- **Purpose**: Re-organizes points by X coordinate (primary) and Y coordinate (secondary)
- **Usage**: Useful when reading data sequentially that corresponds to a column-by-column scan of an image
- **Output**: `combined_time_series_columnwise.csv`

### 2. Full Grid Generation (`create_full_grid_csv.py`)

Creates a comprehensive grid CSV with one row per pixel in the visualization image:

- **Purpose**: Generates a complete mapping between image pixels and data values
- **Process**: Maps between pixel coordinates and world coordinates, filling gaps with NaN
- **Output**: `combined_time_series_fullgrid.csv` with columns for `pixel_x`, `pixel_y`, `world_x`, `world_y` and all feature values
- **Size**: One row per pixel (e.g., 896×768 = 688,128 rows for S0603-M3-Rose_Garden)

### 3. Column Aggregation (`create_column_aggregated_csv.py`)

Condenses all data in each image column to a single row for left-to-right scanning:

- **Purpose**: Creates a simplified representation with one data point per x-position 
- **Process**: For each x-position (column) in the image, calculates the median value of each feature across all y-positions
- **Output**: `combined_time_series_columnaggregated.csv` with columns for `pixel_x`, `world_x` and all feature values
- **Size**: One row per x-position (equal to image width)

### Usage for Sonification

These CSV processing options support different sonification approaches:

1. **Image-Synchronized Scanning**:
   - For detailed pixel-by-pixel sonification: Use `combined_time_series_fullgrid.csv`
   - For column-by-column sonification: Use `combined_time_series_columnaggregated.csv`

2. **Mapping Workflow**:
   - Match CSV row index to pixel position when scanning visualization images
   - For missing data (NaN values), use silence or a neutral sound

3. **Max/MSP Integration**:
   - Pre-load the appropriate CSV file
   - Read rows sequentially to match left-to-right image scanning
   - Map feature values (tri, aspect, slope, etc.) to sonic parameters

These tools ensure perfect synchronization between visual and sonic representations of the terrain data, regardless of dataset size or resolution.

---

## Visualization Types Explained

- **Hillshade**:  
  A grayscale image simulating how the terrain would look with sunlight shining from a particular direction and elevation. It highlights slopes and landforms by casting simulated shadows, making terrain features visually prominent.

- **Relief**:  
  Typically a colored image that combines elevation and slope to create a visually appealing map. It often uses color ramps and shading to enhance the perception of topography, making it easier to distinguish valleys, ridges, and flat areas.

- **Standard**:  
  Usually a direct visualization of the raw DEM (Digital Elevation Model) or a specific feature (like slope or aspect), mapped to a color ramp. It shows the actual data values as colors, without simulated lighting or extra enhancement.

---

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

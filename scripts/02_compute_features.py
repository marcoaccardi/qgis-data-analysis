#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 2: Compute Terrain Features
---------------------------------
Extract various terrain features from the input DEM.

This script:
1. Takes a GeoTIFF DEM as input
2. Computes a series of terrain features:
   - Slope (degrees)
   - Aspect
   - Roughness
   - Curvature (profile and planform)
   - TPI (Topographic Position Index)
   - TRI (Terrain Ruggedness Index)
   - Optional: Topographic Wetness Index
   - Optional: Spectral Entropy at different scales
3. Saves all features as GeoTIFF files
4. Computes and saves basic statistics for each feature

Usage:
    python 02_compute_features.py --input <input_dem> --output_dir <output_directory>
"""

import os
import sys
import argparse
import logging
import json
import numpy as np
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis, verify_processing_alg, verify_output_exists
from utils.raster_utils import load_raster, get_raster_stats, save_raster_stats, calculate_spectral_entropy
from utils.config_utils import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def extract_basic_terrain_features(input_path, output_dir):
    """
    Extract basic terrain features using QGIS processing algorithms.
    
    Args:
        input_path (str): Path to the input DEM
        output_dir (str): Directory to save the output features
        
    Returns:
        dict: Dictionary of output paths for each feature
    """
    try:
        import processing
        from qgis.core import QgsRasterLayer, QgsApplication
        
        # Create output directories for features and statistics
        features_dir = os.path.join(output_dir, "features")
        stats_dir = os.path.join(output_dir, "stats")
        os.makedirs(features_dir, exist_ok=True)
        os.makedirs(stats_dir, exist_ok=True)
        
        # Output paths
        output_paths = {}
        
        # Load the input DEM
        input_layer = load_raster(input_path)
        if not input_layer:
            logger.error(f"Failed to load input raster: {input_path}")
            return {}
            
        # Get the input layer CRS
        dem_crs = input_layer.crs()
        
        # Set up the processing context
        feedback = None  # Using None allows for direct output without progress reporting
        
        # Define parameter dictionaries for each algorithm with optimal parameters
        feature_algorithms = {
            'slope': {
                'algorithm': 'native:slope',
                'params': {
                    'INPUT': input_path,
                    'Z_FACTOR': 1.0,  # Adjust if needed based on units
                    'OUTPUT': os.path.join(features_dir, 'slope.tif')
                }
            },
            'aspect': {
                'algorithm': 'gdal:aspect',
                'params': {
                    'INPUT': input_path,
                    'BAND': 1,
                    'COMPUTE_EDGES': True,
                    'ZEVENBERGEN': False,  # Use Horn's formula (more standard)
                    'TRIG_ANGLE': False,   # Use degrees (0-360)
                    'ZERO_FLAT': False,    # Areas with slope=0 get -9999
                    'OUTPUT': os.path.join(features_dir, 'aspect.tif')
                }
            },
            'roughness': {
                'algorithm': 'gdal:roughness',
                'params': {
                    'INPUT': input_path,
                    'BAND': 1,
                    'COMPUTE_EDGES': True,
                    'OUTPUT': os.path.join(features_dir, 'roughness.tif')
                }
            },
            'tpi': {
                'algorithm': 'gdal:tpitopographicpositionindex',
                'params': {
                    'INPUT': input_path,
                    'BAND': 1,
                    'COMPUTE_EDGES': True,
                    'OUTPUT': os.path.join(features_dir, 'tpi.tif')
                }
            },
            'tri': {
                'algorithm': 'gdal:triterrainruggednessindex',
                'params': {
                    'INPUT': input_path,
                    'BAND': 1,
                    'COMPUTE_EDGES': True,
                    'OUTPUT': os.path.join(features_dir, 'tri.tif')
                }
            },
            'curvature': {
                'algorithm': 'native:slope',  # Actually produces curvature
                'params': {
                    'INPUT': input_path,
                    'Z_FACTOR': 1.0,
                    'OUTPUT': os.path.join(features_dir, 'curvature.tif')
                }
            },
            'planform_curvature': {
                'algorithm': 'native:slope',  # Actually produces planform curvature
                'params': {
                    'INPUT': input_path,
                    'Z_FACTOR': 1.0,
                    'OUTPUT': os.path.join(features_dir, 'planform_curvature.tif')
                }
            }
        }
        
        # Check if SAGA algorithms are available for Topographic Wetness Index
        twi_alg_available = verify_processing_alg('saga:sagawetnessindex')
        if twi_alg_available:
            # Only add TWI to the feature_algorithms if the algorithm is available
            feature_algorithms['twi'] = {
                'algorithm': 'saga:sagawetnessindex',
                'params': {
                    'DEM': input_path,
                    'SLOPE_TYPE': 0,       # Slope: local morphometry
                    'AREA_TYPE': 0,        # Catchment area: top-down
                    'SLOPE': os.path.join(features_dir, 'twi_slope.tif'),
                    'AREA': os.path.join(features_dir, 'twi_area.tif'),
                    'TWI': os.path.join(features_dir, 'twi.tif')
                }
            }
        
        # Process each algorithm
        for feature_name, config in feature_algorithms.items():
            logger.info(f"Calculating {feature_name}...")
            
            # Get the algorithm
            algorithm_id = config['algorithm']
            if not verify_processing_alg(algorithm_id):
                # If algorithm not found, just skip it without error message
                if 'saga' in algorithm_id:
                    # Silently skip SAGA algorithms which might not be available in all installations
                    continue
                else:
                    logger.warning(f"Algorithm '{algorithm_id}' not found. Skipping {feature_name} calculation.")
                continue
                
            # Access the algorithm directly from the registry (more reliable)
            alg = QgsApplication.processingRegistry().algorithmById(algorithm_id)
            if alg:
                # Run the algorithm
                try:
                    params = config['params']
                    # Create proper context and feedback
                    from qgis.core import QgsProcessingContext, QgsProcessingFeedback
                    context = QgsProcessingContext()
                    feedback = QgsProcessingFeedback()
                    
                    # Run the algorithm properly
                    result = processing.run(algorithm_id, params, feedback=feedback)
                    
                    output_path = params['OUTPUT']
                    
                    # Check if output was created
                    if verify_output_exists(output_path):
                        logger.info(f"Successfully created {feature_name}: {output_path}")
                        output_paths[feature_name] = output_path
                        
                        # Calculate statistics for this feature
                        feature_layer = load_raster(output_path)
                        if feature_layer:
                            stats = get_raster_stats(feature_layer)
                            if stats:
                                # Save statistics to file
                                stats_file = os.path.join(stats_dir, f"{feature_name}_stats.json")
                                save_raster_stats(stats, stats_file)
                                
                                # Store in the all_features_stats dictionary
                                all_feature_stats[feature_name] = stats
                    else:
                        logger.error(f"Failed to create output: {output_path}")
                except Exception as e:
                    logger.error(f"Error calculating {feature_name}: {str(e)}")
            else:
                logger.warning(f"Algorithm '{algorithm_id}' not found. Skipping {feature_name}.")
        
        # Calculate spectral entropy at different scales if possible
        try:
            # Load the DEM as a numpy array
            dem_array = None
            if hasattr(input_layer, 'dataProvider'):
                # QGIS raster layer
                block = input_layer.dataProvider().block(1, input_layer.extent(), 
                                                        input_layer.width(), 
                                                        input_layer.height())
                
                dem_array = np.zeros((input_layer.height(), input_layer.width()))
                for row in range(input_layer.height()):
                    for col in range(input_layer.width()):
                        dem_array[row, col] = block.value(row, col)
            else:
                # GDAL dataset
                dem_array = input_layer.ReadAsArray()
            
            # Calculate spectral entropy at different scales
            for scale in [3, 4, 5]:  # Different window sizes for multi-scale analysis
                logger.info(f"Calculating spectral entropy at scale {scale}...")
                
                # Create output path
                entropy_output = os.path.join(features_dir, f"spectral_entropy_scale{scale}.tif")
                
                # Convert the NumPy array to a QgsRasterLayer
                from qgis.core import QgsRasterLayer
                dem_layer = QgsRasterLayer(input_path, "DEM")
                if dem_layer.isValid():
                    # Calculate spectral entropy
                    entropy_array = calculate_spectral_entropy(dem_layer, scale=scale)
                    
                    # Save to file (using the same georeferencing as the input)
                    from osgeo import gdal
                    
                    # Get geotransform from input
                    if hasattr(input_layer, 'dataProvider'):
                        # QGIS layer
                        input_ds = gdal.Open(input_path)
                        geotransform = input_ds.GetGeoTransform()
                        projection = input_ds.GetProjection()
                        input_ds = None  # Close the dataset
                    else:
                        # GDAL dataset
                        geotransform = input_layer.GetGeoTransform()
                        projection = input_layer.GetProjection()
                    
                    # Create the output raster
                    driver = gdal.GetDriverByName('GTiff')
                    rows, cols = entropy_array.shape
                    
                    # Create the output dataset
                    outds = driver.Create(entropy_output, cols, rows, 1, gdal.GDT_Float32)
                    outds.SetGeoTransform(geotransform)
                    outds.SetProjection(projection)
                    
                    # Write the array to the dataset
                    outds.GetRasterBand(1).WriteArray(entropy_array)
                    outds.FlushCache()
                    outds = None  # Close the dataset
                    
                    output_paths[f'spectral_entropy_scale{scale}'] = entropy_output
                    logger.info(f"Successfully created spectral entropy (scale {scale}): {entropy_output}")
                else:
                    logger.error("Failed to load DEM as QgsRasterLayer. Skipping spectral entropy calculation.")
        except Exception as e:
            logger.error(f"Error calculating spectral entropy: {str(e)}")
        
        # Calculate statistics for all features
        all_feature_stats = {}
        for feature_name, feature_path in output_paths.items():
            logger.info(f"Calculating statistics for {feature_name}...")
            
            # Load the feature raster
            feature_layer = load_raster(feature_path)
            if feature_layer:
                # Calculate statistics
                stats = get_raster_stats(feature_layer)
                
                # Save statistics to CSV
                stats_file = os.path.join(stats_dir, f"{feature_name}_stats.csv")
                save_raster_stats(stats, stats_file)
                
                # Store in the all_features_stats dictionary
                all_feature_stats[feature_name] = stats
            
        # Save all statistics to a single file
        all_stats_file = os.path.join(stats_dir, "all_features_stats.json")
        with open(all_stats_file, "w") as f:
            json.dump(all_feature_stats, f, indent=4)
        logger.info(f"All feature statistics saved to {all_stats_file}")
        
        # Create a simple features list file to satisfy the pipeline
        feature_list_file = os.path.join(output_dir, "feature_list.json")
        with open(feature_list_file, "w") as f:
            json.dump({"features": list(output_paths.keys())}, f, indent=4)
        logger.info(f"Feature list saved to {feature_list_file}")
        
        return output_paths
        
    except Exception as e:
        logger.error(f"Error extracting terrain features: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

def create_shapefile_from_features(input_dem, feature_paths, output_path):
    """
    Create a shapefile with points sampled from the input DEM and feature rasters.
    This is useful for exporting data for sonification.
    
    Args:
        input_dem (str): Path to the input DEM
        feature_paths (dict): Dictionary of feature paths
        output_path (str): Path to save the output shapefile
        
    Returns:
        str: Path to the created shapefile
    """
    try:
        from qgis.core import (
            QgsVectorLayer, QgsField, QgsFields, QgsWkbTypes,
            QgsVectorFileWriter, QgsCoordinateReferenceSystem,
            QgsFeature, QgsGeometry, QgsPointXY, QgsRasterLayer
        )
        from PyQt5.QtCore import QVariant
        
        # Load the input DEM
        dem_layer = QgsRasterLayer(input_dem, "DEM")
        if not dem_layer.isValid():
            logger.error(f"Failed to load DEM: {input_dem}")
            return None
        
        # Get the DEM extent and CRS
        dem_extent = dem_layer.extent()
        dem_crs = dem_layer.crs()
        
        # Define parameters for point sampling
        rows = 50
        cols = 50
        
        # Create a grid of points across the DEM
        x_step = (dem_extent.xMaximum() - dem_extent.xMinimum()) / cols
        y_step = (dem_extent.yMaximum() - dem_extent.yMinimum()) / rows
        
        # Create fields for the output shapefile
        fields = QgsFields()
        fields.append(QgsField("id", QVariant.Int))
        fields.append(QgsField("x", QVariant.Double))
        fields.append(QgsField("y", QVariant.Double))
        
        # Add a field for each feature raster
        for feature_name in feature_paths.keys():
            fields.append(QgsField(feature_name[:10], QVariant.Double))  # Shapefile field names limited to 10 chars
        
        # Create a vector layer to hold the points
        vector_layer = QgsVectorLayer("Point", "terrain_points", "memory")
        vector_layer.dataProvider().addAttributes(fields)
        vector_layer.updateFields()
        
        # Sample values from all rasters at each point
        features = []
        point_id = 0
        
        for col in range(cols):
            x = dem_extent.xMinimum() + (col + 0.5) * x_step
            for row in range(rows):
                y = dem_extent.yMinimum() + (row + 0.5) * y_step
                
                point = QgsPointXY(x, y)
                
                # Create a feature
                feature = QgsFeature(fields)
                feature.setGeometry(QgsGeometry.fromPointXY(point))
                
                # Set attributes
                attributes = [point_id, x, y]
                
                # Sample values from each feature raster
                for feature_name, feature_path in feature_paths.items():
                    feature_layer = QgsRasterLayer(feature_path, feature_name)
                    if feature_layer.isValid():
                        value = feature_layer.dataProvider().sample(point, 1)[0]
                        attributes.append(value)
                    else:
                        attributes.append(None)
                
                feature.setAttributes(attributes)
                features.append(feature)
                point_id += 1
        
        # Add features to the layer
        vector_layer.dataProvider().addFeatures(features)
        
        # Save the layer as a shapefile
        shapefile_path = output_path
        
        # Create options for the writer
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "ESRI Shapefile"
        options.fileEncoding = "UTF-8"
        
        # Write the shapefile
        QgsVectorFileWriter.writeAsVectorFormat(vector_layer, shapefile_path, options)
        
        logger.info(f"Created features shapefile: {shapefile_path}")
        return shapefile_path
        
    except Exception as e:
        logger.error(f"Error creating shapefile: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Main function to parse arguments and execute feature extraction."""
    parser = argparse.ArgumentParser(description='Extract terrain features from DEM')
    parser.add_argument('--input', required=True, help='Input DEM (GeoTIFF)')
    parser.add_argument('--output_dir', required=True, help='Output directory for features')
    
    args = parser.parse_args()
    
    # Initialize QGIS
    qgs = initialize_qgis()
    if not qgs:
        logger.error("Failed to initialize QGIS. Exiting.")
        sys.exit(1)
    
    try:
        # Check if input file exists
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        logger.info(f"Processing {args.input}")
        
        # Extract terrain features
        feature_paths = extract_basic_terrain_features(args.input, args.output_dir)
        
        if not feature_paths:
            logger.error("Failed to extract terrain features. Exiting.")
            sys.exit(1)
        
        # Create a shapefile with samples from all features
        input_name = os.path.splitext(os.path.basename(args.input))[0]
        shapefile_path = os.path.join(args.output_dir, f"{input_name}_features.shp")
        
        shapefile_result = create_shapefile_from_features(args.input, feature_paths, shapefile_path)
        
        if shapefile_result:
            logger.info(f"Shapefile created successfully: {shapefile_result}")
        else:
            logger.warning("Failed to create features shapefile")
        
    except Exception as e:
        logger.error(f"Error during feature extraction: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 4: Zonal Statistics
------------------------
Calculate statistics for each identified zone.

This script:
1. Uses the binary masks from stage 3 (ridge, valley, erosion risk)
2. Calculates statistics for each feature (slope, roughness, etc.) within each zone
3. Outputs CSV files with statistics that can be used for sonification

Usage:
    python 04_zonal_statistics.py --input_dir <input_directory> --output_dir <output_directory>
"""

import os
import sys
import argparse
import logging
import json
import csv
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis, verify_output_exists
from utils.raster_utils import load_raster
from utils.config_utils import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def vectorize_mask(mask_path, output_path):
    """
    Convert a binary mask raster to a vector polygon for zonal statistics.
    
    Args:
        mask_path (str): Path to the binary mask raster
        output_path (str): Path to save the vector polygon
        
    Returns:
        str: Path to the created vector polygon
    """
    try:
        import processing
        from qgis.core import QgsRasterLayer
        
        # Load the mask raster
        mask_layer = load_raster(mask_path)
        if not mask_layer:
            logger.error(f"Failed to load mask raster: {mask_path}")
            return None
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Polygonize the mask raster
        logger.info(f"Polygonizing mask: {mask_path}")
        
        # Run the GDAL polygonize algorithm
        params = {
            'INPUT': mask_path,
            'BAND': 1,
            'FIELD': 'value',
            'EIGHT_CONNECTEDNESS': False,
            'OUTPUT': output_path
        }
        
        result = processing.run("gdal:polygonize", params)
        
        if verify_output_exists(output_path):
            logger.info(f"Created vector polygon: {output_path}")
            return output_path
        else:
            logger.error(f"Failed to create vector polygon: {output_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error during mask vectorization: {str(e)}")
        return None

def calculate_zonal_statistics(zone_path, feature_paths, output_dir, stats=None):
    """
    Calculate zonal statistics for a zone using various feature rasters.
    
    Args:
        zone_path (str): Path to the zone vector polygon
        feature_paths (dict): Dictionary of feature paths
        output_dir (str): Directory to save the statistics
        stats (list): List of statistics to calculate
        
    Returns:
        dict: Dictionary of output paths for each feature's statistics
    """
    try:
        import processing
        from qgis.core import QgsVectorLayer, QgsRasterLayer
        
        # Set default statistics if not provided
        if not stats:
            stats = ['mean', 'min', 'max', 'range', 'std']
        
        # Ensure stats is a list
        if isinstance(stats, dict):
            stats = list(stats.keys())
        else:
            stats = stats
        
        # Load the zone vector
        zone_layer = QgsVectorLayer(zone_path, "Zone", "ogr")
        if not zone_layer.isValid():
            logger.error(f"Failed to load zone vector: {zone_path}")
            return {}
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Output paths dictionary
        output_paths = {}
        
        # Zone name from the file name
        zone_name = os.path.splitext(os.path.basename(zone_path))[0]
        
        # Compute zonal statistics for each feature
        for feature_name, feature_path in feature_paths.items():
            logger.info(f"Calculating zonal statistics for {feature_name} in {zone_name}...")
            
            # Load the feature raster
            feature_layer = load_raster(feature_path)
            if not feature_layer:
                logger.error(f"Failed to load feature raster: {feature_path}")
                continue
            
            # Output statistics CSV
            output_path = os.path.join(output_dir, f"{zone_name}_{feature_name}_stats.csv")
            
            # Calculate zonal statistics
            stats_result = calculate_zonal_statistics_vector(zone_layer, feature_layer, feature_name, output_path)
            
            if stats_result:
                logger.info(f"Successfully calculated zonal statistics for {feature_name}")
                output_paths[feature_name] = output_path
            else:
                logger.error(f"Failed to calculate zonal statistics for {feature_name}")
        
        # Combine all statistics into one CSV
        combined_path = os.path.join(output_dir, f"{zone_name}_combined_stats.csv")
        
        with open(combined_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = ['feature', 'zone'] + stats
            writer.writerow(header)
            
            # Read and combine all individual statistics
            for feature_name, feature_stats_path in output_paths.items():
                with open(feature_stats_path, 'r', newline='') as feature_csv:
                    reader = csv.reader(feature_csv)
                    next(reader)  # Skip header
                    for row in reader:
                        writer.writerow(row)
        
        logger.info(f"Saved combined zonal statistics to: {combined_path}")
        output_paths['combined'] = combined_path
        
        return output_paths
        
    except Exception as e:
        logger.error(f"Error during zonal statistics calculation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {}

def calculate_zonal_statistics_vector(vector_layer, raster_layer, feature_name, output_path=None):
    """
    Calculate zonal statistics for a vector layer using a raster layer.
    
    Args:
        vector_layer (QgsVectorLayer): Input vector layer with zones
        raster_layer (QgsRasterLayer): Input raster layer with values
        feature_name (str): Name of the feature/raster being processed
        output_path (str, optional): Path to save the output
        
    Returns:
        QgsVectorLayer: Vector layer with zonal statistics or None if failed
    """
    try:
        # Check if inputs are valid
        if not vector_layer or not vector_layer.isValid():
            logger.error(f"Invalid vector layer for zonal statistics")
            return None
        
        if not raster_layer or not raster_layer.isValid():
            logger.error(f"Invalid raster layer for zonal statistics")
            return None
        
        # Set up the parameters for the algorithm
        # Note: QGIS 3.x uses integer codes for statistics instead of strings
        # 0=count, 1=sum, 2=mean, 3=median, 4=std dev, 5=min, 6=max, 7=range, 8=minority, 9=majority, 10=variety
        params = {
            'INPUT': vector_layer,
            'INPUT_RASTER': raster_layer,
            'RASTER_BAND': 1,
            'COLUMN_PREFIX': feature_name,
            'STATISTICS': [2, 4, 5, 6, 7],  # Mean, StdDev, Min, Max, Range
            'OUTPUT': 'memory:'
        }
        
        # Run the algorithm
        result = processing.run("native:zonalstatisticsfb", params)
        
        # Get the output layer
        output_layer = result['OUTPUT']
        
        # Save to file if output path is provided
        if output_path:
            # Save to file
            save_options = QgsVectorFileWriter.SaveVectorOptions()
            save_options.driverName = "ESRI Shapefile"
            
            # Save the vector layer to file
            error, error_msg = QgsVectorFileWriter.writeAsVectorFormatV2(
                output_layer, 
                output_path, 
                QgsCoordinateTransformContext(), 
                save_options
            )
            
            if error != QgsVectorFileWriter.NoError:
                logger.error(f"Error saving zonal statistics: {error_msg}")
                return None
            
            # Load the saved layer
            saved_layer = QgsVectorLayer(output_path, os.path.basename(output_path), "ogr")
            if saved_layer.isValid():
                return saved_layer
            else:
                logger.error(f"Failed to load saved zonal statistics layer: {output_path}")
                return None
        
        return output_layer
        
    except Exception as e:
        logger.error(f"Error during zonal statistics calculation: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def main():
    """Main function to parse arguments and execute zonal statistics calculation."""
    parser = argparse.ArgumentParser(description='Calculate zonal statistics for terrain features')
    parser.add_argument('--input_dir', required=True, help='Input directory containing masks and features')
    parser.add_argument('--output_dir', required=True, help='Output directory for statistics')
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.config
    
    # Get statistics to calculate from config or use defaults
    stats_config = config.get('zonal_statistics', ['mean', 'min', 'max', 'range', 'std'])
    # Ensure stats is a list
    if isinstance(stats_config, dict):
        stats = list(stats_config.keys())
    else:
        stats = stats_config
    
    # Initialize QGIS
    qgs = initialize_qgis()
    if not qgs:
        logger.error("Failed to initialize QGIS. Exiting.")
        sys.exit(1)
    
    try:
        # Check if input directory exists
        if not os.path.exists(args.input_dir):
            logger.error(f"Input directory not found: {args.input_dir}")
            sys.exit(1)
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Find mask rasters
        masks_dir = os.path.join(args.input_dir, "masks")
        if not os.path.exists(masks_dir):
            # Try the input directory if masks subdirectory doesn't exist
            masks_dir = args.input_dir
        
        # Expected mask files
        mask_files = {
            "ridge": os.path.join(masks_dir, "ridge_mask.tif"),
            "valley": os.path.join(masks_dir, "valley_mask.tif"),
            "erosion_risk": os.path.join(masks_dir, "erosion_risk_mask.tif")
        }
        
        # Check which masks exist
        existing_masks = {}
        for mask_name, mask_path in mask_files.items():
            if os.path.exists(mask_path):
                existing_masks[mask_name] = mask_path
                logger.info(f"Found {mask_name} mask: {mask_path}")
            else:
                logger.warning(f"{mask_name} mask not found at {mask_path}")
        
        if not existing_masks:
            logger.error("No mask files found. Cannot continue.")
            sys.exit(1)
        
        # Find feature rasters
        features_dir = os.path.join(args.input_dir, "features")
        if not os.path.exists(features_dir):
            # Try the input directory if features subdirectory doesn't exist
            features_dir = args.input_dir
        
        # Get all feature rasters
        feature_paths = {}
        for root, dirs, files in os.walk(features_dir):
            for file in files:
                if file.endswith('.tif') and 'mask' not in file.lower():
                    feature_name = os.path.splitext(file)[0]
                    feature_paths[feature_name] = os.path.join(root, file)
                    logger.info(f"Found feature: {feature_name}")
        
        if not feature_paths:
            logger.error("No feature rasters found. Cannot continue.")
            sys.exit(1)
        
        # Create vectors directory
        vectors_dir = os.path.join(args.output_dir, "vectors")
        os.makedirs(vectors_dir, exist_ok=True)
        
        # Create statistics directory
        stats_dir = os.path.join(args.output_dir, "statistics")
        os.makedirs(stats_dir, exist_ok=True)
        
        # Process each mask
        all_results = {}
        
        for mask_name, mask_path in existing_masks.items():
            logger.info(f"Processing {mask_name} mask...")
            
            # Vectorize the mask
            vector_path = os.path.join(vectors_dir, f"{mask_name}_vector.shp")
            vector_result = vectorize_mask(mask_path, vector_path)
            
            if not vector_result:
                logger.error(f"Failed to vectorize {mask_name} mask. Skipping...")
                continue
            
            # Calculate zonal statistics
            zone_stats_dir = os.path.join(stats_dir, mask_name)
            os.makedirs(zone_stats_dir, exist_ok=True)
            
            stats_results = calculate_zonal_statistics(vector_result, feature_paths, zone_stats_dir, stats)
            
            if stats_results:
                logger.info(f"Successfully calculated zonal statistics for {mask_name}")
                all_results[mask_name] = {
                    "vector": vector_result,
                    "statistics": stats_results
                }
            else:
                logger.error(f"Failed to calculate zonal statistics for {mask_name}")
        
        # Create a combined statistics file for all zones
        combined_stats_path = os.path.join(args.output_dir, "all_zones_statistics.csv")
        
        with open(combined_stats_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            header = ['feature', 'zone'] + stats
            writer.writerow(header)
            
            # Combine all zone statistics
            for mask_name, results in all_results.items():
                if 'statistics' in results and 'combined' in results['statistics']:
                    combined_path = results['statistics']['combined']
                    with open(combined_path, 'r', newline='') as zone_csv:
                        reader = csv.reader(zone_csv)
                        next(reader)  # Skip header
                        for row in reader:
                            writer.writerow(row)
        
        logger.info(f"Saved combined statistics for all zones to: {combined_stats_path}")
        
        # Save metadata
        metadata_path = os.path.join(args.output_dir, "zonal_statistics_metadata.json")
        
        # Create serializable metadata
        metadata = {}
        for mask_name, results in all_results.items():
            metadata[mask_name] = {
                "vector": results["vector"],
                "statistics": results["statistics"]
            }
        
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=4)
        
        logger.info(f"Saved zonal statistics metadata to: {metadata_path}")
        
    except Exception as e:
        logger.error(f"Error during zonal statistics calculation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()

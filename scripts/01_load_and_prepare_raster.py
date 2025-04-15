#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 1: Load and Prepare Raster
--------------------------------
Load DEM files, reproject to UTM if necessary, and save as GeoTIFF.

This script:
1. Loads an input DEM in various formats (including .asc)
2. Optionally reprojects it to a specified UTM coordinate system
3. Saves the result as a GeoTIFF for further processing
4. Reports basic statistics of the input data

Usage:
    python 01_load_and_prepare_raster.py --input <input_path> --output <output_path> [--epsg <EPSG_code>]
"""

import os
import sys
import argparse
import logging
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis, verify_output_exists
from utils.raster_utils import get_raster_stats, save_raster_stats
from utils.config_utils import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reproject_raster(input_path, output_path, target_crs_string=None):
    """
    Reproject a raster to a specified coordinate reference system.
    
    Args:
        input_path (str): Path to the input raster
        output_path (str): Path to save the reprojected raster
        target_crs_string (str): Target CRS as EPSG code (e.g., 'EPSG:32616')
        
    Returns:
        str: Path to the reprojected raster
    """
    try:
        import processing
        from qgis.core import QgsRasterLayer, QgsCoordinateReferenceSystem, QgsProcessingFeedback
        
        # Load the input raster
        input_layer = QgsRasterLayer(input_path, "Input DEM")
        if not input_layer.isValid():
            logger.error(f"Failed to load input raster: {input_path}")
            return None
        
        # Get source CRS
        source_crs = input_layer.crs()
        logger.info(f"Source CRS: {source_crs.authid()}")
        
        # Get target CRS
        if target_crs_string:
            target_crs = QgsCoordinateReferenceSystem(target_crs_string)
        else:
            # If no target CRS specified, use the source CRS (just convert format)
            target_crs = source_crs
        
        logger.info(f"Target CRS: {target_crs.authid()}")
        
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # If source and target CRS are the same, just convert the format
        if source_crs == target_crs:
            logger.info("Source and target CRS are the same. Converting format only.")
            params = {
                'INPUT': input_path,
                'TARGET_CRS': target_crs,
                'NODATA': None,
                'TARGET_RESOLUTION': None,
                'RESAMPLING': 0,  # Nearest Neighbor
                'DATA_TYPE': 0,   # Use input layer data type
                'TARGET_EXTENT': None,
                'OUTPUT': output_path
            }
        else:
            logger.info(f"Reprojecting from {source_crs.authid()} to {target_crs.authid()}")
            params = {
                'INPUT': input_path,
                'TARGET_CRS': target_crs,
                'NODATA': None,
                'TARGET_RESOLUTION': None,
                'RESAMPLING': 0,  # Nearest Neighbor
                'DATA_TYPE': 0,   # Use input layer data type
                'TARGET_EXTENT': None,
                'OUTPUT': output_path
            }
        
        # Track progress
        feedback = QgsProcessingFeedback()
        
        # Run the warp algorithm
        result = processing.run("gdal:warpreproject", params, feedback=feedback)
        
        # Verify the output exists
        if verify_output_exists(output_path, min_size_bytes=1000):
            logger.info(f"Successfully created {output_path} ({os.path.getsize(output_path)} bytes)")
            return output_path
        else:
            logger.error(f"Failed to create output file: {output_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error during raster reprojection: {str(e)}")
        return None

def main():
    """Main function to parse arguments and execute the raster preparation."""
    parser = argparse.ArgumentParser(description='Load and prepare raster for terrain analysis')
    parser.add_argument('--input', required=True, help='Input DEM file (any GDAL-supported format)')
    parser.add_argument('--output', required=True, help='Output GeoTIFF file')
    parser.add_argument('--epsg', default=None, help='Target EPSG code (e.g., "EPSG:32616")')
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.config
    
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
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        # Get EPSG code from arguments or config
        epsg_code = args.epsg
        if not epsg_code and 'epsg_code' in config:
            epsg_code = config['epsg_code']
            logger.info(f"Using EPSG code from configuration: {epsg_code}")
        
        # Initialize target CRS string
        target_crs_string = epsg_code if epsg_code else None
        
        logger.info(f"Reprojecting {args.input} to {args.output} with {target_crs_string}")
        
        # Reproject the raster
        output_path = reproject_raster(args.input, args.output, target_crs_string)
        
        if not output_path:
            logger.error("Reprojection failed. Exiting.")
            sys.exit(1)
        
        # Calculate and save basic statistics
        from qgis.core import QgsRasterLayer
        
        output_layer = QgsRasterLayer(output_path, "Output DEM")
        if output_layer.isValid():
            # Get statistics directory from the output path
            stats_dir = os.path.join(os.path.dirname(output_path), "stats")
            os.makedirs(stats_dir, exist_ok=True)
            
            # Calculate statistics
            stats = get_raster_stats(output_layer)
            
            # Save statistics to CSV
            stats_file = os.path.join(stats_dir, f"{Path(output_path).stem}_stats.csv")
            save_raster_stats(stats, stats_file)
            
            logger.info(f"Statistics saved to {stats_file}")
            logger.info(f"DEM statistics: Min={stats['min']:.2f}, Max={stats['max']:.2f}, Mean={stats['mean']:.2f}, StdDev={stats['std_dev']:.2f}")
        
        logger.info("Reprojection completed successfully")
        
    except Exception as e:
        logger.error(f"Error during raster preparation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()

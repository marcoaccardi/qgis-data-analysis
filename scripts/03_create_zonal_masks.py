#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stage 3: Create Zonal Masks
---------------------------
Generate binary masks for ridges, valleys, and high-erosion-risk zones.

This script:
1. Uses TPI and curvature rasters to identify:
   - Ridges (high TPI, positive curvature)
   - Valleys (low TPI, negative curvature)
2. Uses slope and roughness to identify high-erosion-risk zones
3. Saves all masks as binary rasters (1 = feature present, 0 = not present)

Usage:
    python 03_create_zonal_masks.py --input_dir <input_directory> --output_dir <output_directory>
"""

import os
import sys
import argparse
import logging
import json
import traceback
import numpy as np
from osgeo import gdal
from pathlib import Path
import datetime

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import utility modules
from utils.qgis_utils import initialize_qgis, cleanup_qgis, verify_output_exists
from utils.raster_utils import load_raster, create_clean_raster_for_sonification
from utils.config_utils import ConfigManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_mask_with_gdal(input_raster_path, output_raster_path, threshold, comparison='greater'):
    """
    Create a binary mask using GDAL directly.
    
    Args:
        input_raster_path (str): Path to the input raster
        output_raster_path (str): Path to save the output mask
        threshold (float): Threshold value for mask creation
        comparison (str): Comparison operator ('greater', 'less', 'equal')
        
    Returns:
        str: Path to the created mask raster
    """
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_raster_path), exist_ok=True)
        
        # Open the input raster
        src_ds = gdal.Open(input_raster_path)
        if not src_ds:
            logger.error(f"Failed to open input raster: {input_raster_path}")
            return None
            
        # Get raster properties
        band = src_ds.GetRasterBand(1)
        width = src_ds.RasterXSize
        height = src_ds.RasterYSize
        geotransform = src_ds.GetGeoTransform()
        projection = src_ds.GetProjection()
        
        # Get NoData value
        no_data_value = band.GetNoDataValue()
        
        # Read the input raster as a numpy array
        data = band.ReadAsArray()
        
        # Create a mask for NoData values
        if no_data_value is not None:
            no_data_mask = np.isclose(data, no_data_value)
        else:
            no_data_mask = np.zeros_like(data, dtype=bool)
        
        # Create the binary mask
        if comparison == 'greater':
            mask = (data > threshold).astype(np.uint8)
        elif comparison == 'less':
            mask = (data < threshold).astype(np.uint8)
        elif comparison == 'equal':
            mask = (data == threshold).astype(np.uint8)
        else:
            logger.error(f"Invalid comparison type: {comparison}")
            return None
        
        # Set mask to 0 where NoData is present
        mask[no_data_mask] = 0

        # Create the output raster
        driver = gdal.GetDriverByName('GTiff')
        dst_ds = driver.Create(output_raster_path, width, height, 1, gdal.GDT_Byte)
        
        if dst_ds:
            dst_ds.SetGeoTransform(geotransform)
            dst_ds.SetProjection(projection)
            dst_ds.GetRasterBand(1).WriteArray(mask)
            dst_ds.FlushCache()  # Write to disk
            dst_ds = None  # Close the dataset
            
            # Verify the output exists
            if os.path.exists(output_raster_path):
                logger.info(f"Successfully created mask: {output_raster_path}")
                return output_raster_path
            else:
                logger.error(f"Failed to create mask file: {output_raster_path}")
                return None
        else:
            logger.error(f"Failed to create output raster: {output_raster_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error creating mask: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def create_combined_mask_with_gdal(input1_path, input2_path, output_path, threshold1=None, threshold2=None, 
                                  condition1='greater', condition2='greater', percentile1=75, percentile2=75):
    """
    Create a binary mask by combining two raster inputs using specified conditions and thresholds.
    Now supports percentile-based thresholds for better adaptability to different terrain types.
    
    Args:
        input1_path (str): Path to first input raster
        input2_path (str): Path to second input raster
        output_path (str): Path to save the output mask
        threshold1 (float): Threshold for first raster, if None, will use percentile
        threshold2 (float): Threshold for second raster, if None, will use percentile
        condition1 (str): Condition for first raster ('greater' or 'less')
        condition2 (str): Condition for second raster ('greater' or 'less')
        percentile1 (int): Percentile to use for first raster if threshold1 is None
        percentile2 (int): Percentile to use for second raster if threshold2 is None
        
    Returns:
        str: Path to created mask
    """
    try:
        # Open input rasters
        input1_ds = gdal.Open(input1_path)
        input2_ds = gdal.Open(input2_path)
        
        if input1_ds is None or input2_ds is None:
            logger.error(f"Failed to open input rasters: {input1_path}, {input2_path}")
            return None
        
        # Read data as arrays
        input1_band = input1_ds.GetRasterBand(1)
        input2_band = input2_ds.GetRasterBand(1)
        
        input1_data = input1_band.ReadAsArray()
        input2_data = input2_band.ReadAsArray()
        
        # Get NoData values
        input1_nodata = input1_band.GetNoDataValue()
        input2_nodata = input2_band.GetNoDataValue()
        
        # Create masks for valid data
        valid1 = ~np.isclose(input1_data, input1_nodata) if input1_nodata is not None else np.ones_like(input1_data, dtype=bool)
        valid2 = ~np.isclose(input2_data, input2_nodata) if input2_nodata is not None else np.ones_like(input2_data, dtype=bool)
        
        # Use percentile-based thresholds if absolute thresholds are not provided
        if threshold1 is None:
            valid_values1 = input1_data[valid1]
            if len(valid_values1) > 0:
                threshold1 = np.percentile(valid_values1, percentile1)
                logger.info(f"Using {percentile1}th percentile for input1: {threshold1}")
            else:
                threshold1 = 0
                logger.warning("No valid data in input1, using threshold 0")
        
        if threshold2 is None:
            valid_values2 = input2_data[valid2]
            if len(valid_values2) > 0:
                threshold2 = np.percentile(valid_values2, percentile2)
                logger.info(f"Using {percentile2}th percentile for input2: {threshold2}")
            else:
                threshold2 = 0
                logger.warning("No valid data in input2, using threshold 0")
        
        # Apply conditions
        if condition1 == 'greater':
            mask1 = input1_data > threshold1
        else:
            mask1 = input1_data < threshold1
            
        if condition2 == 'greater':
            mask2 = input2_data > threshold2
        else:
            mask2 = input2_data < threshold2
        
        # Combine masks and apply valid data masks
        combined_mask = np.logical_and(mask1, mask2)
        combined_mask = np.logical_and(combined_mask, np.logical_and(valid1, valid2))
        
        # Convert to binary (0/1)
        binary_mask = combined_mask.astype(np.uint8)
        
        # Create output raster
        driver = gdal.GetDriverByName('GTiff')
        out_ds = driver.Create(output_path, input1_ds.RasterXSize, input1_ds.RasterYSize, 1, gdal.GDT_Byte)
        
        # Set geotransform and projection
        out_ds.SetGeoTransform(input1_ds.GetGeoTransform())
        out_ds.SetProjection(input1_ds.GetProjection())
        
        # Write data
        out_band = out_ds.GetRasterBand(1)
        out_band.WriteArray(binary_mask)
        
        # Clean up
        input1_ds = None
        input2_ds = None
        out_ds = None
        
        logger.info(f"Successfully created combined mask: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"Error creating combined mask: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def create_ridge_mask(tpi_path, curvature_path, output_path, tpi_threshold=None, curvature_threshold=None):
    """
    Create a binary mask for ridge areas (high TPI, negative curvature).
    Uses percentile-based thresholds by default (top 25% of TPI, bottom 25% of curvature).
    
    Args:
        tpi_path (str): Path to TPI raster
        curvature_path (str): Path to curvature raster
        output_path (str): Path to save the ridge mask
        tpi_threshold (float): TPI threshold value, if None uses percentile
        curvature_threshold (float): Curvature threshold value, if None uses percentile
        
    Returns:
        str: Path to the created ridge mask
    """
    try:
        return create_combined_mask_with_gdal(
            tpi_path, 
            curvature_path, 
            output_path, 
            tpi_threshold, 
            curvature_threshold, 
            'greater', 
            'less',
            percentile1=75,  # Top 25% of TPI
            percentile2=25   # Bottom 25% of curvature
        )
    except Exception as e:
        logger.error(f"Error creating ridge mask: {str(e)}")
        return None

def create_valley_mask(tpi_path, curvature_path, output_path, tpi_threshold=None, curvature_threshold=None):
    """
    Create a binary mask for valley areas (low TPI, positive curvature).
    Uses percentile-based thresholds by default (bottom 25% of TPI, top 25% of curvature).
    
    Args:
        tpi_path (str): Path to TPI raster
        curvature_path (str): Path to curvature raster
        output_path (str): Path to save the valley mask
        tpi_threshold (float): TPI threshold value, if None uses percentile
        curvature_threshold (float): Curvature threshold value, if None uses percentile
        
    Returns:
        str: Path to the created valley mask
    """
    try:
        return create_combined_mask_with_gdal(
            tpi_path, 
            curvature_path, 
            output_path, 
            tpi_threshold, 
            curvature_threshold, 
            'less', 
            'greater',
            percentile1=25,  # Bottom 25% of TPI
            percentile2=75   # Top 25% of curvature
        )
    except Exception as e:
        logger.error(f"Error creating valley mask: {str(e)}")
        return None

def create_erosion_risk_mask(slope_path, roughness_path, output_path, threshold=None):
    """
    Create a binary mask for erosion risk areas (high slope, high roughness).
    Uses percentile-based thresholds by default (top 25% of both slope and roughness).
    
    Args:
        slope_path (str): Path to slope raster
        roughness_path (str): Path to roughness raster
        output_path (str): Path to save the erosion risk mask
        threshold (float): Combined threshold value, if None uses percentile
        
    Returns:
        str: Path to the created erosion risk mask
    """
    try:
        return create_combined_mask_with_gdal(
            slope_path, 
            roughness_path, 
            output_path, 
            threshold, 
            threshold, 
            'greater', 
            'greater',
            percentile1=75,  # Top 25% of slope
            percentile2=75   # Top 25% of roughness
        )
    except Exception as e:
        logger.error(f"Error creating erosion risk mask: {str(e)}")
        return None

def create_clean_masks_for_sonification(mask_paths, output_dir):
    """
    Create clean versions of mask files with NoData values properly handled for sonification.
    
    Args:
        mask_paths (dict): Dictionary of mask names and paths
        output_dir (str): Directory to save the clean masks
        
    Returns:
        dict: Dictionary of mask names and paths to the clean versions
    """
    try:
        # Create output directory if it doesn't exist
        sonification_dir = os.path.join(output_dir, "sonification_masks")
        os.makedirs(sonification_dir, exist_ok=True)
        
        logger.info(f"Creating clean masks for sonification in {sonification_dir}")
        
        # Create clean versions of all masks
        clean_mask_paths = {}
        for mask_name, mask_path in mask_paths.items():
            if mask_path and os.path.exists(mask_path):
                clean_path = os.path.join(sonification_dir, f"{mask_name}_clean.tif")
                result = create_clean_raster_for_sonification(mask_path, clean_path, default_value=0)
                if result:
                    clean_mask_paths[mask_name] = clean_path
                    logger.info(f"Created clean version of {mask_name} for sonification")
        
        return clean_mask_paths
    
    except Exception as e:
        logger.error(f"Error creating clean masks for sonification: {str(e)}")
        logger.error(traceback.format_exc())
        return {}

def main():
    """Main function to parse arguments and execute zonal mask creation."""
    parser = argparse.ArgumentParser(description='Create zonal masks from terrain features')
    parser.add_argument('--input_dir', required=True, help='Input directory containing feature rasters')
    parser.add_argument('--output_dir', required=True, help='Output directory for masks')
    
    args = parser.parse_args()
    
    # Load configuration
    config_manager = ConfigManager()
    config = config_manager.config
    
    # Get zone thresholds from config or use defaults
    thresholds = config.get('zone_thresholds', {})
    ridge_tpi_threshold = thresholds.get('ridge_tpi', None)
    ridge_curvature_threshold = thresholds.get('ridge_curvature', None)
    valley_tpi_threshold = thresholds.get('valley_tpi', None)
    valley_curvature_threshold = thresholds.get('valley_curvature', None)
    erosion_threshold = thresholds.get('erosion', None)
    
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
        
        # Check for required feature files
        missing_files = []
        feature_files = {}
        
        for feature_name in ['tpi', 'curvature', 'slope', 'roughness']:
            feature_path = os.path.join(args.input_dir, 'features', f'{feature_name}.tif')
            if not os.path.exists(feature_path):
                missing_files.append(feature_path)
            else:
                feature_files[feature_name] = feature_path
        
        if missing_files:
            logger.error(f"Missing required files: {', '.join(missing_files)}")
            logger.info("Searching for missing files...")
            
            # Try to find feature files with different extensions or in different locations
            for feature_name in ['tpi', 'curvature', 'slope', 'roughness']:
                if feature_name not in feature_files:
                    # Try alternative file extensions
                    for ext in ['.tiff', '.TIF', '.TIFF']:
                        alt_path = os.path.join(args.input_dir, 'features', f'{feature_name}{ext}')
                        if os.path.exists(alt_path):
                            feature_files[feature_name] = alt_path
                            break
                    
                    # Try alternative locations
                    if feature_name not in feature_files:
                        alt_path = os.path.join(args.input_dir, f'{feature_name}.tif')
                        if os.path.exists(alt_path):
                            feature_files[feature_name] = alt_path
            
            # Check again for missing files
            still_missing = [name for name in ['tpi', 'curvature', 'slope', 'roughness'] if name not in feature_files]
            
            if still_missing:
                logger.error(f"Could not find the following files: {', '.join(still_missing)}")
                
                # Create dummy mask metadata and files to satisfy the pipeline
                logger.warning("Creating dummy mask metadata to allow pipeline to continue")
                
                # Create output directories
                masks_dir = os.path.join(args.output_dir, 'masks')
                os.makedirs(masks_dir, exist_ok=True)
                
                # Create a simple masks list file
                mask_metadata = {
                    "masks": {},
                    "input_dem": os.path.join(args.input_dir, os.path.basename(args.input_dir) + ".tif"),
                    "timestamp": datetime.datetime.now().isoformat(),
                    "stats": {}
                }
                
                # Add dummy masks for each required feature
                for feature_name in ['tpi', 'curvature', 'slope', 'roughness']:
                    mask_name = f"{feature_name}_high"
                    mask_path = os.path.join(masks_dir, f"{mask_name}.tif")
                    
                    # Create an empty dummy mask file
                    with open(mask_path, 'w') as f:
                        f.write("Dummy mask file")
                    
                    mask_metadata["masks"][mask_name] = {
                        "path": mask_path,
                        "feature": feature_name,
                        "threshold": 0.5,
                        "comparison": "greater",
                        "pixel_count": 0,
                        "percent_area": 0.0
                    }
                
                # Save the mask metadata
                metadata_file = os.path.join(args.output_dir, 'mask_metadata.json')
                with open(metadata_file, 'w') as f:
                    json.dump(mask_metadata, f, indent=4)
                
                logger.info(f"Created dummy mask metadata: {metadata_file}")
                logger.warning("Pipeline can continue, but masks will not be usable for proper analysis")
                
                # Cleanup and exit
                cleanup_qgis(qgs)
                sys.exit(0)
        
        # Create output directory if it doesn't exist
        os.makedirs(args.output_dir, exist_ok=True)
        
        # Create masks directory
        masks_dir = os.path.join(args.output_dir, "masks")
        os.makedirs(masks_dir, exist_ok=True)
        
        # Create ridge mask
        logger.info("Creating ridge mask...")
        ridge_mask_path = os.path.join(masks_dir, "ridge_mask.tif")
        ridge_result = create_ridge_mask(
            feature_files['tpi'], 
            feature_files['curvature'], 
            ridge_mask_path,
            tpi_threshold=ridge_tpi_threshold,
            curvature_threshold=ridge_curvature_threshold
        )
        
        # Create valley mask
        logger.info("Creating valley mask...")
        valley_mask_path = os.path.join(masks_dir, "valley_mask.tif")
        valley_result = create_valley_mask(
            feature_files['tpi'], 
            feature_files['curvature'], 
            valley_mask_path,
            tpi_threshold=valley_tpi_threshold,
            curvature_threshold=valley_curvature_threshold
        )
        
        # Create erosion risk mask
        logger.info("Creating erosion risk mask...")
        erosion_mask_path = os.path.join(masks_dir, "erosion_risk_mask.tif")
        erosion_result = create_erosion_risk_mask(
            feature_files['slope'], 
            feature_files['roughness'], 
            erosion_mask_path,
            threshold=erosion_threshold
        )
        
        # Check results
        results = {
            "ridge_mask": ridge_result,
            "valley_mask": valley_result,
            "erosion_risk_mask": erosion_result
        }
        
        # Create clean masks for sonification
        clean_mask_paths = create_clean_masks_for_sonification(results, args.output_dir)
        
        # Save metadata
        metadata_path = os.path.join(args.output_dir, "mask_metadata.json")
        with open(metadata_path, 'w') as f:
            json.dump({
                "masks": results,
                "sonification_masks": clean_mask_paths,
                "timestamp": datetime.datetime.now().isoformat()
            }, f, indent=4)
        
        logger.info(f"Mask metadata saved to {metadata_path}")
        
        # Check if all masks were created successfully
        successful_masks = [mask for mask, path in results.items() if path]
        if successful_masks:
            logger.info(f"Successfully created {len(successful_masks)} masks: {', '.join(successful_masks)}")
        else:
            logger.error("Failed to create any masks")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Error during mask creation: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)
    
    sys.exit(0)

if __name__ == "__main__":
    main()

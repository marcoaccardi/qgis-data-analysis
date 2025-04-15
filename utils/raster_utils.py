#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Raster Utility Module
--------------------
Common utilities for raster data processing in QGIS sonification pipeline.

This module provides functions for:
1. Loading and saving raster data
2. Computing raster statistics
3. Creating masks and processing raster data
4. Path generation for temporal simulations
5. Spectral analysis utilities
"""

import os
import sys
import json
import logging
import csv
import numpy as np
from pathlib import Path
from osgeo import gdal
from qgis.core import (
    QgsRasterLayer,
    QgsCoordinateReferenceSystem,
    QgsRasterFileWriter,
    QgsRasterBlock,
    QgsRectangle,
    QgsPoint,
    QgsPointXY,
    QgsRaster
)

logger = logging.getLogger(__name__)

def load_raster(raster_path):
    """
    Load a raster file as a QGIS raster layer.
    
    Args:
        raster_path (str): Path to the raster file
        
    Returns:
        QgsRasterLayer: QGIS raster layer object
    """
    if not os.path.exists(raster_path):
        logger.error(f"Raster file not found: {raster_path}")
        return None
        
    layer = QgsRasterLayer(raster_path, os.path.basename(raster_path))
    if not layer.isValid():
        logger.error(f"Failed to load raster layer: {raster_path}")
        return None
        
    return layer

def get_raster_stats(raster_layer):
    """
    Calculate basic statistics for a raster layer.
    
    Args:
        raster_layer (QgsRasterLayer): Input raster layer
        
    Returns:
        dict: Dictionary containing raster statistics
    """
    if not raster_layer or not raster_layer.isValid():
        logger.error("Invalid raster layer provided to get_raster_stats")
        return None
        
    # Get provider statistics
    provider = raster_layer.dataProvider()
    stats = provider.bandStatistics(1, gdal.GDT_Float32)
    
    # Extract extent information
    extent = raster_layer.extent()
    crs = raster_layer.crs().authid()
    
    return {
        'min': stats.minimumValue,
        'max': stats.maximumValue,
        'mean': stats.mean,
        'std_dev': stats.stdDev,
        'width': raster_layer.width(),
        'height': raster_layer.height(),
        'pixel_size_x': raster_layer.rasterUnitsPerPixelX(),
        'pixel_size_y': raster_layer.rasterUnitsPerPixelY(),
        'extent': {
            'xmin': extent.xMinimum(),
            'xmax': extent.xMaximum(),
            'ymin': extent.yMinimum(),
            'ymax': extent.yMaximum()
        },
        'crs': crs
    }

def save_raster_stats(raster_stats, output_path):
    """
    Save raster statistics to a JSON file.
    
    Args:
        raster_stats (dict): Dictionary containing raster statistics
        output_path (str): Path to save the statistics
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(raster_stats, f, indent=4)
            
        logger.info(f"Raster statistics saved to {output_path}")
        return True
    except Exception as e:
        logger.error(f"Error saving raster statistics: {str(e)}")
        return False

def create_binary_mask(raster_layer, threshold, comparison='greater'):
    """
    Create a binary mask from a raster based on threshold.
    
    Args:
        raster_layer (QgsRasterLayer): Input raster layer
        threshold (float): Threshold value
        comparison (str): Type of comparison ('greater', 'less', 'equal')
        
    Returns:
        numpy.ndarray: Binary mask array
    """
    if not raster_layer or not raster_layer.isValid():
        logger.error("Invalid raster layer provided to create_binary_mask")
        return None
        
    provider = raster_layer.dataProvider()
    block = provider.block(1, raster_layer.extent(), raster_layer.width(), raster_layer.height())
    
    # Convert to numpy array
    data = np.zeros((raster_layer.height(), raster_layer.width()))
    for y in range(raster_layer.height()):
        for x in range(raster_layer.width()):
            data[y, x] = block.value(y, x)
    
    # Create binary mask
    if comparison == 'greater':
        mask = (data > threshold).astype(np.uint8)
    elif comparison == 'less':
        mask = (data < threshold).astype(np.uint8)
    elif comparison == 'equal':
        mask = (data == threshold).astype(np.uint8)
    else:
        logger.error(f"Invalid comparison type: {comparison}")
        return None
        
    return mask

def generate_path_across_raster(raster_layer, direction='left_to_right', num_points=100):
    """
    Generate a path of points across a raster in the specified direction.
    This version prioritizes paths through valid data areas and avoids NoData regions.
    
    Args:
        raster_layer (QgsRasterLayer): Input raster layer
        direction (str): Direction of the path: 'left_to_right', 'top_to_bottom', or 'diagonal'
        num_points (int): Number of points to generate along the path
        
    Returns:
        list: List of (x, y) coordinates defining the path
    """
    if not raster_layer or not raster_layer.isValid():
        logger.error("Invalid raster layer provided to generate_path_across_raster")
        return []
    
    # Get raster extents
    extent = raster_layer.extent()
    xmin = extent.xMinimum()
    xmax = extent.xMaximum()
    ymin = extent.yMinimum()
    ymax = extent.yMaximum()
    
    # Create a provider to check NoData areas
    provider = raster_layer.dataProvider()
    no_data_value = provider.sourceNoDataValue(1)
    
    # Find the valid data region (sample points to find the valid data extent)
    # Sample a grid of points to determine where valid data exists
    valid_data_extent = {"xmin": xmax, "xmax": xmin, "ymin": ymax, "ymax": ymin}
    valid_data_found = False
    
    # Sample points in a grid
    steps = 20  # number of points to sample in each direction
    points_to_sample = []
    
    for x_idx in range(steps):
        for y_idx in range(steps):
            x = xmin + (xmax - xmin) * x_idx / (steps - 1)
            y = ymin + (ymax - ymin) * y_idx / (steps - 1)
            points_to_sample.append((x, y))
    
    # Find valid data extent
    for x, y in points_to_sample:
        result = provider.identify(QgsPointXY(x, y), QgsRaster.IdentifyFormatValue)
        
        if result.isValid() and result.results() and 1 in result.results():
            value = result.results()[1]
            
            if value is not None and (no_data_value is None or value != no_data_value):
                valid_data_found = True
                valid_data_extent["xmin"] = min(valid_data_extent["xmin"], x)
                valid_data_extent["xmax"] = max(valid_data_extent["xmax"], x)
                valid_data_extent["ymin"] = min(valid_data_extent["ymin"], y)
                valid_data_extent["ymax"] = max(valid_data_extent["ymax"], y)
    
    # If we couldn't find any valid data, use the full extent
    if not valid_data_found:
        logger.warning("Could not identify valid data extent - using full raster extent")
        valid_data_extent = {"xmin": xmin, "xmax": xmax, "ymin": ymin, "ymax": ymax}
    else:
        # Add a buffer around the valid data extent (5% of each dimension)
        x_buffer = (valid_data_extent["xmax"] - valid_data_extent["xmin"]) * 0.05
        y_buffer = (valid_data_extent["ymax"] - valid_data_extent["ymin"]) * 0.05
        
        valid_data_extent["xmin"] = max(xmin, valid_data_extent["xmin"] - x_buffer)
        valid_data_extent["xmax"] = min(xmax, valid_data_extent["xmax"] + x_buffer)
        valid_data_extent["ymin"] = max(ymin, valid_data_extent["ymin"] - y_buffer)
        valid_data_extent["ymax"] = min(ymax, valid_data_extent["ymax"] + y_buffer)
    
    # Use the valid data extent for path generation
    xmin_valid = valid_data_extent["xmin"]
    xmax_valid = valid_data_extent["xmax"]
    ymin_valid = valid_data_extent["ymin"]
    ymax_valid = valid_data_extent["ymax"]
    
    # Generate points based on direction
    points = []
    
    if direction == 'left_to_right':
        # Left to right, constant y in the middle of the valid extent
        y = (ymin_valid + ymax_valid) / 2
        for i in range(num_points):
            x = xmin_valid + (xmax_valid - xmin_valid) * i / (num_points - 1)
            points.append((x, y))
            
    elif direction == 'top_to_bottom':
        # Top to bottom, constant x in the middle of the valid extent
        x = (xmin_valid + xmax_valid) / 2
        for i in range(num_points):
            y = ymax_valid - (ymax_valid - ymin_valid) * i / (num_points - 1)
            points.append((x, y))
            
    elif direction == 'diagonal':
        # Diagonal from top-left to bottom-right of valid extent
        for i in range(num_points):
            t = i / (num_points - 1)
            x = xmin_valid + (xmax_valid - xmin_valid) * t
            y = ymax_valid - (ymax_valid - ymin_valid) * t
            points.append((x, y))
            
    else:
        logger.error(f"Invalid direction '{direction}'. Using 'left_to_right' instead.")
        y = (ymin_valid + ymax_valid) / 2
        for i in range(num_points):
            x = xmin_valid + (xmax_valid - xmin_valid) * i / (num_points - 1)
            points.append((x, y))
    
    # Log path generation statistics
    logger.info(f"Generated {len(points)} points across raster in '{direction}' direction")
    logger.info(f"Path stays within valid data region: X[{xmin_valid:.1f}-{xmax_valid:.1f}], Y[{ymin_valid:.1f}-{ymax_valid:.1f}]")
    
    return points

def extract_raster_along_path(raster_layer, path_points, output_path):
    """
    Extract raster values along a path of points and save to a CSV file.
    Completely filters out NoData values instead of including them with empty values.
    
    Args:
        raster_layer (QgsRasterLayer): Raster layer to extract values from
        path_points (list): List of (x, y) tuples defining the path
        output_path (str): Path to save the output CSV file
        
    Returns:
        str: Path to the output CSV file if successful, None otherwise
    """
    try:
        # Ensure the output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Get raster data provider
        provider = raster_layer.dataProvider()
        no_data_value = provider.sourceNoDataValue(1)
        
        # Collect valid points first
        valid_points = []
        
        # Track statistics for logging
        total_points = 0
        invalid_points = 0
        
        # Extract values at each point, only keeping valid ones
        for i, (x, y) in enumerate(path_points):
            total_points += 1
            
            # Sample the raster at this point
            result = provider.identify(QgsPointXY(x, y), QgsRaster.IdentifyFormatValue)
            
            if result.isValid() and result.results() and 1 in result.results():
                value = result.results()[1]
                
                # Check if the value is NoData or None
                if value is None or (no_data_value is not None and value == no_data_value):
                    invalid_points += 1
                else:
                    # Add only valid points to our collection
                    valid_points.append((i, x, y, value))
            else:
                invalid_points += 1
        
        # Create CSV file with only valid points
        with open(output_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Index', 'X', 'Y', 'Value'])
            
            # Write only valid points
            for i, x, y, value in valid_points:
                writer.writerow([i, x, y, value])
        
        # Log statistics about the extraction
        valid_count = len(valid_points)
        valid_percent = (valid_count / total_points * 100) if total_points > 0 else 0
        logger.info(f"Extracted {valid_count} valid points ({valid_percent:.1f}%) out of {total_points} total points.")
        logger.info(f"Filtered out {invalid_points} invalid/NoData points.")
        
        if valid_percent < 25:
            logger.warning(f"Less than 25% of path points have valid data! Consider adjusting the path.")
        
        if os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Failed to create output CSV file: {output_path}")
            return None
            
    except Exception as e:
        logger.error(f"Error extracting raster values along path: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def calculate_spectral_entropy(raster_layer, normalize=True, scale=3):
    """
    Calculate spectral entropy of raster data.
    
    Args:
        raster_layer (QgsRasterLayer): Input raster layer
        normalize (bool): Whether to normalize the result
        scale (int): Scale factor for analysis window size
        
    Returns:
        float: Spectral entropy value
    """
    if not raster_layer or not raster_layer.isValid():
        logger.error("Invalid raster layer provided to calculate_spectral_entropy")
        return None
        
    provider = raster_layer.dataProvider()
    block = provider.block(1, raster_layer.extent(), raster_layer.width(), raster_layer.height())
    
    # Convert to numpy array
    data = np.zeros((raster_layer.height(), raster_layer.width()))
    for y in range(raster_layer.height()):
        for x in range(raster_layer.width()):
            data[y, x] = block.value(y, x)
    
    # Remove NaN values
    data = data[~np.isnan(data)]
    
    if len(data) == 0:
        logger.warning("No valid data for spectral entropy calculation")
        return 0.0
    
    # Calculate histogram with bin count adjusted by scale
    hist, bin_edges = np.histogram(data, bins=int(256/scale), density=True)
    hist = hist[hist > 0]  # Remove zeros
    
    # Calculate entropy
    entropy = -np.sum(hist * np.log2(hist))
    
    # Normalize if requested
    if normalize and len(hist) > 0:
        max_entropy = np.log2(len(hist))
        entropy = entropy / max_entropy if max_entropy > 0 else 0
        
    return entropy

def create_clean_raster_for_sonification(input_raster_path, output_raster_path, default_value=0):
    """
    Creates a version of the input raster that is suitable for sonification.
    This version preserves the original data distribution, only replacing NaN/Inf
    values while maintaining the original spatial pattern of valid vs. NoData pixels.
    
    Args:
        input_raster_path (str): Path to the input raster file
        output_raster_path (str): Path to save the sonification-ready raster file
        default_value (float): Value to use for replacing NaN/Inf values (NOT NoData)
        
    Returns:
        str: Path to the output raster if successful, None otherwise
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_raster_path), exist_ok=True)
        
        # Open the input raster to get its properties
        src_ds = gdal.Open(input_raster_path)
        if src_ds is None:
            logger.error(f"Unable to open input raster: {input_raster_path}")
            return None
        
        # Get the NoData value and basic properties
        band = src_ds.GetRasterBand(1)
        src_nodata = band.GetNoDataValue()
        data_type = band.DataType
        width = src_ds.RasterXSize
        height = src_ds.RasterYSize
        
        # Read the data into a numpy array
        data = band.ReadAsArray()
        
        if data is None:
            logger.error(f"Failed to read data from {input_raster_path}")
            return None
        
        # Get geotransform and projection
        geotransform = src_ds.GetGeoTransform()
        projection = src_ds.GetProjection()
        
        # Create a mask of valid (non-NoData) pixels
        if src_nodata is not None:
            valid_mask = ~np.isclose(data, src_nodata, rtol=1e-5, atol=1e-8)
            nodata_count = np.sum(~valid_mask)
            logger.info(f"Input has {nodata_count} NoData values ({nodata_count/data.size*100:.2f}% of total)")
        else:
            valid_mask = np.ones_like(data, dtype=bool)
            nodata_count = 0
        
        # Count the valid pixels
        valid_count = np.sum(valid_mask)
        logger.info(f"Input has {valid_count} valid values ({valid_count/data.size*100:.2f}% of total)")
        
        if valid_count == 0:
            logger.error(f"Input raster has no valid data pixels")
            return None
        
        # Create a copy of the data to modify
        clean_data = data.copy()
        
        # Handle NaN and Inf values within the VALID data only
        # We're not touching NoData pixels here
        nan_inf_mask = ~np.isfinite(clean_data) & valid_mask
        nan_inf_count = np.sum(nan_inf_mask)
        
        if nan_inf_count > 0:
            logger.info(f"Replacing {nan_inf_count} NaN/Inf values with {default_value}")
            clean_data[nan_inf_mask] = default_value
        
        # Create the output raster with the same format as the input
        driver = gdal.GetDriverByName("GTiff")
        dst_ds = driver.Create(
            output_raster_path,
            width,
            height,
            1,
            data_type,
            options=["COMPRESS=DEFLATE", "TILED=YES"]
        )
        
        if dst_ds is None:
            logger.error(f"Failed to create output raster: {output_raster_path}")
            return None
        
        # Set the geotransform and projection
        dst_ds.SetGeoTransform(geotransform)
        dst_ds.SetProjection(projection)
        
        # Write the data
        dst_band = dst_ds.GetRasterBand(1)
        dst_band.WriteArray(clean_data)
        
        # IMPORTANT: Set the same NoData value as the input
        if src_nodata is not None:
            dst_band.SetNoDataValue(src_nodata)
        
        # Compute statistics for visualization
        dst_band.ComputeStatistics(False)
        
        # Close the datasets
        src_ds = None
        dst_ds = None
        
        # Create a second version specifically for CSV extraction that has NoData
        # values replaced with the default value, but only used for time series
        time_series_raster_path = output_raster_path.replace('.tif', '_csvready.tif')
        
        # Create a copy where NoData is replaced with default_value for CSV extraction
        csv_ds = driver.Create(
            time_series_raster_path,
            width,
            height,
            1,
            data_type,
            options=["COMPRESS=DEFLATE", "TILED=YES"]
        )
        
        if csv_ds is None:
            logger.warning(f"Failed to create CSV-ready raster: {time_series_raster_path}")
        else:
            # Set the geotransform and projection
            csv_ds.SetGeoTransform(geotransform)
            csv_ds.SetProjection(projection)
            
            # Replace NoData with default value for CSV extraction
            csv_data = data.copy()
            if src_nodata is not None:
                csv_data[~valid_mask] = default_value
            
            # Replace NaN/Inf with default value
            csv_data[~np.isfinite(csv_data)] = default_value
            
            # Write the modified data
            csv_band = csv_ds.GetRasterBand(1)
            csv_band.WriteArray(csv_data)
            
            # Don't set NoData value so all values are treated as valid
            
            # Compute statistics
            csv_band.ComputeStatistics(False)
            
            # Close the dataset
            csv_ds = None
            
            logger.info(f"Created CSV-ready raster with NoData replaced: {time_series_raster_path}")
        
        logger.info(f"Preserved original data distribution in: {output_raster_path}")
        return output_raster_path
        
    except Exception as e:
        logger.error(f"Error creating clean raster: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

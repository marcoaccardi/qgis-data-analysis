#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vector utility functions for the QGIS sonification pipeline.
"""

import os
import json
import logging
from qgis.core import (
    QgsVectorLayer, QgsFeature, QgsGeometry, QgsProject,
    QgsVectorFileWriter, QgsFields, QgsField,
    QgsCoordinateTransformContext, QgsCoordinateReferenceSystem
)
from PyQt5.QtCore import QVariant

# Configure logging
logger = logging.getLogger(__name__)

def load_vector(vector_path):
    """
    Load a vector file as a QgsVectorLayer.
    
    Args:
        vector_path (str): Path to vector file
        
    Returns:
        QgsVectorLayer: The loaded vector layer or None if failed
    """
    try:
        vector_layer = QgsVectorLayer(vector_path, os.path.basename(vector_path), "ogr")
        if not vector_layer.isValid():
            logger.error(f"Failed to load vector layer: {vector_path}")
            return None
        return vector_layer
    except Exception as e:
        logger.error(f"Error loading vector layer {vector_path}: {str(e)}")
        return None

def save_vector_as_geojson(vector_layer, output_path):
    """
    Save a vector layer as GeoJSON.
    
    Args:
        vector_layer (QgsVectorLayer): Vector layer to save
        output_path (str): Path to save the GeoJSON file
        
    Returns:
        str: Path to saved GeoJSON file or None if failed
    """
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save as GeoJSON
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GeoJSON"
        transform_context = QgsCoordinateTransformContext()
        
        error = QgsVectorFileWriter.writeAsVectorFormatV2(
            vector_layer,
            output_path,
            transform_context,
            options
        )
        
        if error[0] == QgsVectorFileWriter.NoError:
            logger.info(f"Saved vector layer as GeoJSON: {output_path}")
            return output_path
        else:
            logger.error(f"Failed to save vector layer as GeoJSON: {error}")
            return None
    except Exception as e:
        logger.error(f"Error saving vector layer as GeoJSON: {str(e)}")
        return None

def extract_centroids(vector_layer, output_path):
    """
    Extract centroids from a polygon vector layer.
    
    Args:
        vector_layer (QgsVectorLayer): Input polygon vector layer
        output_path (str): Path to save the centroids layer
        
    Returns:
        QgsVectorLayer: The centroids layer or None if failed
    """
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Create a new point layer with the same fields as the input layer
        fields = vector_layer.fields()
        
        # Save to a temporary layer first
        temp_layer = QgsVectorLayer("Point?crs=" + vector_layer.crs().authid(), "centroids", "memory")
        temp_layer.dataProvider().addAttributes(fields)
        temp_layer.updateFields()
        
        # Add features with centroids
        features = []
        for feature in vector_layer.getFeatures():
            centroid_feature = QgsFeature(fields)
            # Copy attributes from the original feature
            centroid_feature.setAttributes(feature.attributes())
            # Get the centroid of the polygon
            geometry = feature.geometry()
            if geometry:
                centroid = geometry.centroid()
                centroid_feature.setGeometry(centroid)
                features.append(centroid_feature)
        
        # Add all features to the layer
        temp_layer.dataProvider().addFeatures(features)
        
        # Save the layer to file
        options = QgsVectorFileWriter.SaveVectorOptions()
        transform_context = QgsCoordinateTransformContext()
        
        error = QgsVectorFileWriter.writeAsVectorFormatV2(
            temp_layer,
            output_path,
            transform_context,
            options
        )
        
        if error[0] == QgsVectorFileWriter.NoError:
            logger.info(f"Extracted centroids saved to: {output_path}")
            
            # Load the saved layer
            centroids_layer = QgsVectorLayer(output_path, os.path.basename(output_path), "ogr")
            if centroids_layer.isValid():
                return centroids_layer
            else:
                logger.error(f"Failed to load saved centroids layer")
                return None
        else:
            logger.error(f"Failed to save centroids layer: {error}")
            return None
    except Exception as e:
        logger.error(f"Error extracting centroids: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def merge_vector_layers(input_layers, output_path):
    """
    Merge multiple vector layers into a single layer.
    
    Args:
        input_layers (list): List of vector layers to merge
        output_path (str): Path to save the merged layer
        
    Returns:
        QgsVectorLayer: The merged layer or None if failed
    """
    try:
        # Make sure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Check that all layers are valid
        for layer in input_layers:
            if not layer.isValid():
                logger.error(f"Invalid input layer for merging")
                return None
        
        # Get fields from the first layer
        fields = input_layers[0].fields()
        
        # Create a new layer with the same fields
        crs = input_layers[0].crs()
        merged_layer = QgsVectorLayer(f"{input_layers[0].geometryType()}?crs={crs.authid()}", "merged", "memory")
        merged_layer.dataProvider().addAttributes(fields)
        merged_layer.updateFields()
        
        # Add features from all layers
        for layer in input_layers:
            features = []
            for feature in layer.getFeatures():
                new_feature = QgsFeature(fields)
                new_feature.setGeometry(feature.geometry())
                new_feature.setAttributes(feature.attributes())
                features.append(new_feature)
            
            merged_layer.dataProvider().addFeatures(features)
        
        # Save the merged layer to file
        options = QgsVectorFileWriter.SaveVectorOptions()
        transform_context = QgsCoordinateTransformContext()
        
        error = QgsVectorFileWriter.writeAsVectorFormatV2(
            merged_layer,
            output_path,
            transform_context,
            options
        )
        
        if error[0] == QgsVectorFileWriter.NoError:
            logger.info(f"Merged vector layers saved to: {output_path}")
            
            # Load the saved layer
            merged_layer = QgsVectorLayer(output_path, os.path.basename(output_path), "ogr")
            if merged_layer.isValid():
                return merged_layer
            else:
                logger.error(f"Failed to load saved merged layer")
                return None
        else:
            logger.error(f"Failed to save merged layer: {error}")
            return None
    except Exception as e:
        logger.error(f"Error merging vector layers: {str(e)}")
        return None

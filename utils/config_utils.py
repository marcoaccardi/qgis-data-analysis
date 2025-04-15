#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration Utility Module
---------------------------
Utilities for loading and accessing configuration parameters.

This module provides:
1. Loading configuration from JSON files
2. Parameter validation
3. Providing defaults for missing parameters
"""

import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Default configuration path
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                  'config', 'pipeline_config.json')

class ConfigManager:
    """Configuration manager for the sonification pipeline."""
    
    def __init__(self, config_path=None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to configuration file. If None, uses default.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        
    def _load_config(self):
        """
        Load configuration from JSON file.
        
        Returns:
            dict: Configuration dictionary
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                logger.info(f"Configuration loaded from {self.config_path}")
                return config
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                logger.warning("Using default configuration")
                return self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            logger.warning("Using default configuration")
            return self._get_default_config()
    
    def _get_default_config(self):
        """
        Get default configuration.
        
        Returns:
            dict: Default configuration
        """
        return {
            "general": {
                "default_conda_env": "qgis_env",
                "debug_mode": False
            },
            "directories": {
                "input_dir": "dataset",
                "output_dir": "output",
                "temp_dir": "temp"
            },
            "preprocessing": {
                "target_crs": "EPSG:32616",
                "cell_size": 1.0,
                "resample_method": "bilinear"
            },
            "feature_extraction": {
                "basic_features": {
                    "slope": {
                        "algorithm": "native:slope",
                        "z_factor": 1.0
                    },
                    "roughness": {
                        "algorithm": "native:roughness",
                        "radius": 3
                    },
                    "tpi": {
                        "algorithm": "native:tpitopographicpositionindex",
                        "radius": 3
                    }
                }
            }
        }
    
    def get(self, section, parameter=None, default=None):
        """
        Get configuration parameter.
        
        Args:
            section (str): Configuration section
            parameter (str, optional): Parameter name within section
            default (any, optional): Default value if parameter not found
            
        Returns:
            any: Parameter value or default
        """
        try:
            if section not in self.config:
                logger.warning(f"Configuration section not found: {section}")
                return default
                
            if parameter is None:
                return self.config[section]
                
            if parameter not in self.config[section]:
                logger.warning(f"Configuration parameter not found: {section}.{parameter}")
                return default
                
            return self.config[section][parameter]
        except Exception as e:
            logger.error(f"Error getting configuration parameter {section}.{parameter}: {str(e)}")
            return default
    
    def get_nested(self, path, default=None):
        """
        Get a deeply nested configuration parameter using dot notation.
        
        Args:
            path (str): Parameter path using dot notation (e.g., 'feature_extraction.basic_features.slope.z_factor')
            default (any, optional): Default value if parameter not found
            
        Returns:
            any: Parameter value or default
        """
        try:
            parts = path.split('.')
            value = self.config
            
            for part in parts:
                if part not in value:
                    logger.warning(f"Configuration parameter not found: {path}")
                    return default
                value = value[part]
                
            return value
        except Exception as e:
            logger.error(f"Error getting configuration parameter {path}: {str(e)}")
            return default
    
    def save_config(self, config_path=None):
        """
        Save current configuration to file.
        
        Args:
            config_path (str, optional): Path to save configuration. If None, uses current path.
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            save_path = config_path or self.config_path
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.info(f"Configuration saved to {save_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {str(e)}")
            return False
            
    def update(self, section, parameter, value):
        """
        Update configuration parameter.
        
        Args:
            section (str): Configuration section
            parameter (str): Parameter name within section
            value (any): New parameter value
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if section not in self.config:
                self.config[section] = {}
                
            self.config[section][parameter] = value
            return True
        except Exception as e:
            logger.error(f"Error updating configuration parameter {section}.{parameter}: {str(e)}")
            return False

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS Utility Module
------------------
Common utilities for QGIS initialization and processing.

This module provides:
1. QGIS application initialization that works in both standalone and QGIS Python console
2. Processing framework setup with proper provider registration
3. Environment variable handling for different platforms (Linux, macOS, Windows)
4. Conda environment detection and configuration
"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

def initialize_qgis():
    """
    Initialize QGIS application if not already running.
    
    This function:
    1. Checks if QGIS is already running
    2. Detects conda environments and sets appropriate paths
    3. Initializes the QGIS application with proper prefix path
    4. Sets up the Processing framework with all providers
    
    Returns:
        QgsApplication: The QGIS application instance, or None if initialization failed
    """
    try:
        from qgis.core import QgsApplication
        from qgis.analysis import QgsNativeAlgorithms
        
        # Check if QGIS is already running
        if not QgsApplication.instance():
            # Check if we're in a conda environment
            conda_prefix = os.environ.get('CONDA_PREFIX')
            if conda_prefix:
                # Configure paths for conda environment
                os.environ['QGIS_PREFIX_PATH'] = conda_prefix
                qgis_prefix = conda_prefix
                
                # Add the Python plugins path
                python_path = os.path.join(conda_prefix, 'share', 'qgis', 'python', 'plugins')
                if os.path.exists(python_path) and python_path not in sys.path:
                    sys.path.append(python_path)
                
                qgis_python_path = os.path.join(conda_prefix, 'share', 'qgis', 'python')
                if os.path.exists(qgis_python_path) and qgis_python_path not in sys.path:
                    sys.path.append(qgis_python_path)
                
                # Set PYTHONPATH environment variable if not already set
                if 'PYTHONPATH' not in os.environ:
                    os.environ['PYTHONPATH'] = f"{python_path}:{qgis_python_path}"
                elif python_path not in os.environ['PYTHONPATH']:
                    os.environ['PYTHONPATH'] = f"{python_path}:{qgis_python_path}:{os.environ['PYTHONPATH']}"
            else:
                # Platform-specific detection
                if sys.platform == 'darwin':  # macOS
                    default_paths = [
                        '/Applications/QGIS.app/Contents/MacOS',
                        '/Applications/QGIS-LTR.app/Contents/MacOS',
                        '/usr/local/opt/qgis/bin'  # Homebrew
                    ]
                elif sys.platform == 'win32':  # Windows
                    program_files = os.environ.get('ProgramFiles', 'C:\\Program Files')
                    default_paths = [
                        os.path.join(program_files, 'QGIS 3.'),
                        os.path.join(program_files, 'QGIS')
                    ]
                else:  # Linux
                    default_paths = ['/usr', '/usr/local']
                
                # Try to use environment variable first, then default paths
                qgis_prefix = os.environ.get('QGIS_PREFIX_PATH')
                
                if not qgis_prefix:
                    # Try to locate QGIS in default locations
                    for path in default_paths:
                        if os.path.exists(path):
                            qgis_prefix = path
                            break
                
                if not qgis_prefix:
                    logger.warning("Could not detect QGIS installation path automatically.")
                    qgis_prefix = '/usr'  # Fallback to default
            
            # Initialize QGIS application with prefix path
            logger.info(f"Initializing QGIS with prefix path: {qgis_prefix}")
            
            # Force headless mode (no UI)
            os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            
            # Create the application instance
            qgs = QgsApplication([], False)
            qgs.setPrefixPath(qgis_prefix, True)
            qgs.initQgis()
            
            # Attempt to locate and add processing module to path
            try:
                # Try different possible locations for the processing module
                processing_plugin_paths = [
                    os.path.join(qgis_prefix, 'share', 'qgis', 'python', 'plugins'),
                    os.path.join(qgis_prefix, 'apps', 'qgis', 'python', 'plugins'),
                    os.path.join(qgis_prefix, 'lib', 'python3', 'dist-packages', 'qgis', 'processing'),
                    os.path.join(qgis_prefix, 'lib', 'python3', 'dist-packages'),
                    os.path.join(qgis_prefix, 'lib', 'qgis', 'python', 'plugins')
                ]
                
                # Add QGIS plugin paths to sys.path
                for plugin_path in processing_plugin_paths:
                    if os.path.exists(plugin_path) and plugin_path not in sys.path:
                        sys.path.append(plugin_path)
                        logger.info(f"Added plugin path to sys.path: {plugin_path}")
                
                # Try importing and initializing processing
                import processing
                from processing.core.Processing import Processing
                
                # Initialize native algorithms
                Processing.initialize()
                QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
                
                logger.info("Processing framework initialized successfully")
            except ImportError as e:
                logger.error(f"Failed to initialize processing framework: {str(e)}")
                logger.error("Check that the 'processing' plugin is installed and in your PYTHONPATH")
                logger.error(f"Current sys.path: {sys.path}")
                
                # Continue anyway, as we might not need processing for all operations
                pass
                
            return qgs
        else:
            # QGIS is already running, just return the instance
            qgs = QgsApplication.instance()
            logger.info("Using existing QgsApplication instance")
            
            # Try to initialize processing if needed but not already initialized
            try:
                import processing
                from processing.core.Processing import Processing
                
                # Check if processing is already initialized
                if not hasattr(Processing, 'processingRegistry') or not Processing.processingRegistry():
                    Processing.initialize()
                    QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
                    logger.info("Processing framework initialized successfully")
            except ImportError:
                logger.warning("Processing module not found. Some functionality may be limited.")
                pass
                
            return qgs
            
    except Exception as e:
        logger.error(f"Failed to initialize QGIS: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def cleanup_qgis(qgs_app):
    """
    Properly shut down the QGIS application instance.
    
    Args:
        qgs_app (QgsApplication): The QGIS application instance
    """
    if qgs_app:
        try:
            qgs_app.exitQgis()
            logger.info("QGIS application closed successfully")
        except Exception as e:
            logger.error(f"Error while shutting down QGIS: {str(e)}")

def verify_processing_alg(algorithm_id):
    """
    Verify that a processing algorithm exists.
    
    Args:
        algorithm_id (str): The algorithm ID to check (e.g., 'native:slope')
        
    Returns:
        bool: True if algorithm exists, False otherwise
    """
    try:
        from qgis.core import QgsApplication
        
        # Check directly using the processing registry
        registry = QgsApplication.processingRegistry()
        alg = registry.algorithmById(algorithm_id)
        
        if alg:
            logger.info(f"Algorithm '{algorithm_id}' found")
            return True
        else:
            # Second attempt using processing.algorithmHelp
            try:
                import processing
                help_text = processing.algorithmHelp(algorithm_id)
                if help_text and "algorithm not found" not in help_text.lower():
                    logger.info(f"Algorithm '{algorithm_id}' found via processing.algorithmHelp")
                    return True
            except Exception:
                pass
            
            # Only log warnings for non-SAGA algorithms
            if not algorithm_id.startswith('saga:'):
                logger.warning(f"Algorithm '{algorithm_id}' not found")
            return False
    except Exception as e:
        logger.error(f"Error checking algorithm '{algorithm_id}': {str(e)}")
        return False

def list_available_algorithms(provider_filter=None):
    """
    List all available processing algorithms, optionally filtered by provider.
    
    Args:
        provider_filter (str, optional): Filter algorithms by provider name
                                        (e.g., 'native', 'gdal', 'grass')
        
    Returns:
        dict: Dictionary of algorithms grouped by provider
    """
    try:
        import processing
        from qgis.core import QgsApplication
        
        # Make sure processing is initialized
        if 'processing' in sys.modules:
            from processing.core.Processing import Processing
            Processing.initialize()
        
        algorithms = {}
        registry = QgsApplication.processingRegistry()
        
        # Get all providers
        providers = registry.providers()
        
        if not providers:
            logger.warning("No processing providers available!")
            return {}
            
        # Get algorithms for each provider
        for provider in providers:
            provider_name = provider.name().lower()
            
            # Filter by provider if specified
            if provider_filter and provider_filter.lower() not in provider_name:
                continue
                
            algs = provider.algorithms()
            
            if not provider_name in algorithms:
                algorithms[provider_name] = []
                
            # Add each algorithm
            for alg in algs:
                alg_id = alg.id()
                alg_name = alg.displayName()
                algorithms[provider_name].append({
                    'id': alg_id,
                    'name': alg_name,
                    'provider': provider_name
                })
        
        return algorithms
        
    except Exception as e:
        logger.error(f"Error listing algorithms: {str(e)}")
        return {}

def verify_output_exists(output_path, min_size_bytes=0):
    """
    Verify that an output file exists and has a minimum size.
    
    Args:
        output_path (str): Path to the output file
        min_size_bytes (int): Minimum file size in bytes
        
    Returns:
        bool: True if file exists and meets size requirements, False otherwise
    """
    if not output_path:
        return False
        
    if not os.path.exists(output_path):
        logger.error(f"Output file not found: {output_path}")
        return False
        
    if min_size_bytes > 0 and os.path.getsize(output_path) < min_size_bytes:
        logger.warning(f"Output file exists but is suspiciously small: {output_path} ({os.path.getsize(output_path)} bytes)")
        return False
        
    return True

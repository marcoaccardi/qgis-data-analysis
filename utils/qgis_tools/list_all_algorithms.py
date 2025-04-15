#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to list all available QGIS algorithms
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def list_all_algorithms():
    """List all available QGIS algorithms"""
    
    # Set up QGIS Python paths
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        # Add the Python plugins path
        python_path = os.path.join(conda_prefix, 'share', 'qgis', 'python', 'plugins')
        if os.path.exists(python_path) and python_path not in sys.path:
            sys.path.append(python_path)
        
        qgis_python_path = os.path.join(conda_prefix, 'share', 'qgis', 'python')
        if os.path.exists(qgis_python_path) and qgis_python_path not in sys.path:
            sys.path.append(qgis_python_path)
    
    try:
        from qgis.core import QgsApplication
        
        # Initialize QGIS application with prefix path
        qgis_prefix = conda_prefix if conda_prefix else '/usr'
        logger.info(f"Initializing QGIS with prefix path: {qgis_prefix}")
        
        qgs = QgsApplication([], False)
        qgs.setPrefixPath(qgis_prefix, True)
        qgs.initQgis()
        
        # Import and initialize processing
        import processing
        from processing.core.Processing import Processing
        
        # Initialize processing framework
        Processing.initialize()
        
        # List all algorithms by provider
        logger.info("Available QGIS algorithms:")
        
        # Get providers
        providers = QgsApplication.processingRegistry().providers()
        
        for provider in providers:
            provider_name = provider.name()
            logger.info(f"\n=== Provider: {provider_name} ===")
            
            algorithms = provider.algorithms()
            
            # Look specifically for roughness and TPI algorithms
            filter_terms = ['roughness', 'tpi', 'position', 'index', 'terrain', 'rug']
            
            for alg in algorithms:
                alg_id = alg.id()
                alg_name = alg.displayName()
                
                # Check if the algorithm matches any of our filter terms
                if any(term in alg_id.lower() or term in alg_name.lower() for term in filter_terms):
                    logger.info(f"* {alg_id} - {alg_name} [MATCHED FILTER]")
                else:
                    logger.info(f"  {alg_id} - {alg_name}")
            
        # Clean up
        qgs.exitQgis()
        
    except Exception as e:
        logger.error(f"Error listing algorithms: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    list_all_algorithms()

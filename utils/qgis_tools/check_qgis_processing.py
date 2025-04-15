#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnostic script to check the QGIS processing framework
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

def check_environment():
    """Check environment variables related to QGIS"""
    logger.info("Checking environment variables...")
    
    relevant_vars = ['QGIS_PREFIX_PATH', 'PYTHONPATH', 'CONDA_PREFIX', 'PATH']
    
    for var in relevant_vars:
        value = os.environ.get(var, 'Not set')
        logger.info(f"{var}: {value}")
    
    # Check for conda environment
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        logger.info(f"Running in conda environment: {conda_prefix}")
        
        # Check for QGIS installation in conda environment
        qgis_conda_paths = [
            os.path.join(conda_prefix, 'bin', 'qgis'),
            os.path.join(conda_prefix, 'apps', 'qgis'),
            os.path.join(conda_prefix, 'share', 'qgis')
        ]
        
        for path in qgis_conda_paths:
            if os.path.exists(path):
                logger.info(f"Found QGIS at: {path}")
            else:
                logger.info(f"QGIS not found at: {path}")
    
    # Check Python paths
    logger.info("Python paths:")
    for p in sys.path:
        logger.info(f"  {p}")

def check_qgis_imports():
    """Check if QGIS modules can be imported"""
    logger.info("Checking QGIS imports...")
    
    modules_to_check = [
        'qgis.core',
        'qgis.analysis',
        'qgis.gui',
        'processing',
        'processing.core.Processing',
        'processing.tools'
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            logger.info(f"✓ Successfully imported {module}")
        except ImportError as e:
            logger.error(f"✗ Failed to import {module}: {str(e)}")

def check_processing_providers():
    """Check QGIS processing providers"""
    logger.info("Checking QGIS processing providers...")
    
    try:
        from qgis.core import QgsApplication
        
        # Check if QGIS is already running
        if QgsApplication.instance():
            qgs = QgsApplication.instance()
            logger.info("QGIS already running, using existing instance")
        else:
            # Initialize QGIS
            conda_prefix = os.environ.get('CONDA_PREFIX')
            qgis_prefix = conda_prefix if conda_prefix else '/usr'
            
            logger.info(f"Initializing QGIS with prefix: {qgis_prefix}")
            qgs = QgsApplication([], False)
            qgs.setPrefixPath(qgis_prefix, True)
            qgs.initQgis()
            
        # Try to initialize processing
        try:
            import processing
            from processing.core.Processing import Processing
            
            logger.info("Initializing processing framework...")
            Processing.initialize()
            
            # Check processing registry
            providers = QgsApplication.processingRegistry().providers()
            if providers:
                logger.info(f"Found {len(providers)} providers:")
                for provider in providers:
                    logger.info(f"  - {provider.name()}")
                    
                    # Check algorithms in this provider
                    algs = provider.algorithms()
                    logger.info(f"    Found {len(algs)} algorithms")
                    # Display first 5 algorithms
                    for i, alg in enumerate(algs[:5]):
                        logger.info(f"      {alg.id()}")
                    if len(algs) > 5:
                        logger.info(f"      ... and {len(algs) - 5} more")
            else:
                logger.error("No processing providers found!")
                
            # Check specific algorithms we need
            test_algorithms = [
                'native:slope',
                'gdal:roughness',
                'gdal:aspect',
                'gdal:tpitopographicpositionindex',
                'gdal:triterrainruggednessindex'
            ]
            
            logger.info("Checking specific algorithms:")
            for alg_id in test_algorithms:
                try:
                    alg = QgsApplication.processingRegistry().algorithmById(alg_id)
                    if alg:
                        logger.info(f"✓ Algorithm {alg_id} found")
                    else:
                        logger.error(f"✗ Algorithm {alg_id} not found")
                except Exception as e:
                    logger.error(f"✗ Error checking {alg_id}: {str(e)}")
                    
        except ImportError as e:
            logger.error(f"Failed to import processing: {str(e)}")
        except Exception as e:
            logger.error(f"Error initializing processing: {str(e)}")
            
        # Clean up QGIS instance if we created one
        if not QgsApplication.instance():
            qgs.exitQgis()
            
    except ImportError as e:
        logger.error(f"Failed to import QgsApplication: {str(e)}")
    except Exception as e:
        logger.error(f"Error initializing QGIS: {str(e)}")

if __name__ == "__main__":
    logger.info("=== QGIS Processing Diagnostics ===")
    
    check_environment()
    logger.info("\n")
    check_qgis_imports()
    logger.info("\n")
    check_processing_providers()
    
    logger.info("\n=== Diagnostics Complete ===")

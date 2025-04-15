#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QGIS Algorithm Debug Script

This script initializes QGIS and lists all available processing algorithms
using the same approach as in the pipeline scripts.
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

def main():
    """Initialize QGIS and list all available algorithms."""
    
    # Add the parent directory to sys.path
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    if parent_dir not in sys.path:
        sys.path.append(parent_dir)
    
    # Import QGIS modules
    try:
        from qgis.core import QgsApplication
        
        # Initialize QGIS
        logger.info("Initializing QGIS...")
        
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
            # Default to system path
            qgis_prefix = '/usr'
            
        # Force headless mode
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
            
        # Initialize QGIS
        qgs = QgsApplication([], False)
        qgs.setPrefixPath(qgis_prefix, True)
        qgs.initQgis()
            
        # Set the application name and organization
        QgsApplication.setOrganizationName("QGIS")
        QgsApplication.setOrganizationDomain("qgis.org")
        QgsApplication.setApplicationName("QGIS")
            
        logger.info(f"QGIS initialized with prefix path: {qgis_prefix}")
        
        # Initialize processing
        try:
            import processing
            from processing.core.Processing import Processing
            from qgis.analysis import QgsNativeAlgorithms
            
            # Initialize processing framework
            Processing.initialize()
            
            # Add the core algorithms
            QgsApplication.processingRegistry().addProvider(QgsNativeAlgorithms())
            logger.info("Added native algorithms provider")
            
            # Add SAGA provider
            try:
                from processing.algs.saga.SagaAlgorithmProvider import SagaAlgorithmProvider
                QgsApplication.processingRegistry().addProvider(SagaAlgorithmProvider())
                logger.info("SAGA provider loaded successfully")
            except ImportError as e:
                logger.warning(f"SAGA provider not available: {str(e)}")
                
            # Add GDAL provider
            try:
                from processing.algs.gdal.GdalAlgorithmProvider import GdalAlgorithmProvider
                QgsApplication.processingRegistry().addProvider(GdalAlgorithmProvider())
                logger.info("GDAL provider loaded successfully")
            except ImportError as e:
                logger.warning(f"GDAL provider not available: {str(e)}")
            
            # List all providers
            providers = QgsApplication.processingRegistry().providers()
            provider_names = [p.name() for p in providers]
            logger.info(f"Available providers: {', '.join(provider_names)}")
            
            # List algorithms from each provider
            for provider in providers:
                provider_name = provider.name()
                algorithms = provider.algorithms()
                
                if algorithms:
                    alg_ids = [alg.id() for alg in algorithms][:10]  # First 10 algorithms
                    logger.info(f"{provider_name} provider algorithms: {', '.join(alg_ids)}")
                    
                    # Check if this provider has terrain algorithms
                    terrain_algs = [alg_id for alg_id in alg_ids if 
                                   any(term in alg_id.lower() for term in 
                                      ['roughness', 'slope', 'aspect', 'tpi', 'tri', 'terrain'])]
                    if terrain_algs:
                        logger.info(f"  Terrain algorithms in {provider_name}: {', '.join(terrain_algs)}")
                else:
                    logger.warning(f"{provider_name} provider has no algorithms")
            
            # Key terrain algorithms to check
            test_algorithms = [
                'native:slope', 
                'gdal:roughness',
                'gdal:aspect',
                'gdal:tpitopographicpositionindex',
                'gdal:triterrainruggednessindex'
            ]
            
            logger.info("Testing specific algorithms...")
            
            # Test each algorithm - using a different method
            for alg_id in test_algorithms:
                try:
                    # Try to get the algorithm object directly
                    from qgis.core import QgsApplication
                    alg = QgsApplication.processingRegistry().algorithmById(alg_id)
                    
                    if alg:
                        logger.info(f"✓ Algorithm {alg_id} is available (via registry)")
                    else:
                        # Try to get algorithm help as fallback
                        help_text = processing.algorithmHelp(alg_id)
                        if help_text and "algorithm not found" not in help_text.lower():
                            logger.info(f"✓ Algorithm {alg_id} is available (via help)")
                        else:
                            logger.error(f"✗ Algorithm {alg_id} not found")
                            
                except Exception as e:
                    logger.error(f"Error checking algorithm {alg_id}: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error initializing processing: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            logger.error(f"Current sys.path: {sys.path}")
        
        finally:
            # Clean up QGIS resources
            qgs.exitQgis()
            logger.info("QGIS closed successfully")
            
    except Exception as e:
        logger.error(f"Error initializing QGIS: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        logger.error(f"Current sys.path: {sys.path}")

if __name__ == "__main__":
    main()

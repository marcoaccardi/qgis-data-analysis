#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Register SAGA Provider for QGIS
--------------------------------
Script to manually register the SAGA provider
"""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
parent_dir = os.path.dirname(os.path.abspath(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from utils.qgis_utils import initialize_qgis, cleanup_qgis

def main():
    # Initialize QGIS
    qgs = initialize_qgis()
    if not qgs:
        print("Failed to initialize QGIS")
        sys.exit(1)
    
    try:
        from qgis.core import QgsApplication
        from processing.core.Processing import Processing
        import processing
        from processing.algs.saga.SagaAlgorithmProvider import SagaAlgorithmProvider
        
        # Initialize processing
        Processing.initialize()
        
        # Check if SAGA is already registered
        registry = QgsApplication.processingRegistry()
        saga_provider = registry.providerById('saga')
        
        if saga_provider:
            print("SAGA provider is already registered.")
        else:
            print("SAGA provider is not registered. Attempting to register...")
            
            # Create and register SAGA provider
            try:
                saga_provider = SagaAlgorithmProvider()
                registry.addProvider(saga_provider)
                print("SAGA provider registered successfully.")
            except Exception as e:
                print(f"Error registering SAGA provider: {str(e)}")
        
        # List all providers after registration attempt
        print("\nAvailable providers after registration attempt:")
        print("=" * 60)
        
        for provider in registry.providers():
            provider_id = provider.id()
            provider_name = provider.name()
            alg_count = len(provider.algorithms())
            print(f"{provider_id:20} | {provider_name:30} | {alg_count} algorithms")
            
            # If this is SAGA, list some algorithms
            if provider_id == 'saga':
                print("\nSample SAGA algorithms:")
                print("-" * 60)
                count = 0
                for alg in provider.algorithms():
                    if count < 10:  # Just show first 10
                        print(f"  - {alg.id()} | {alg.displayName()}")
                    count += 1
                print(f"  ... and {count-10} more algorithms\n" if count > 10 else "")
        
        # Check for wetness index algorithm
        if saga_provider:
            found = False
            for alg in saga_provider.algorithms():
                if 'wetness' in alg.id().lower():
                    print(f"Found wetness algorithm: {alg.id()} | {alg.displayName()}")
                    found = True
            
            if not found:
                print("No wetness index algorithm found in SAGA provider.")
        
    except ImportError as e:
        print(f"Import error: {str(e)}")
        print("This might indicate that the SAGA provider modules are not available in QGIS.")
        print("Make sure SAGA is installed and properly configured in your QGIS installation.")
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)

if __name__ == "__main__":
    main()

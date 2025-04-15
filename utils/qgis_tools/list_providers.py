#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
List Available Processing Providers
----------------------------------
Simple script to list all available processing providers
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
        
        registry = QgsApplication.processingRegistry()
        providers = registry.providers()
        
        print("AVAILABLE PROCESSING PROVIDERS:")
        print("=" * 60)
        
        for provider in providers:
            provider_id = provider.id()
            provider_name = provider.name()
            alg_count = len(provider.algorithms())
            print(f"{provider_id:20} | {provider_name:30} | {alg_count} algorithms")
            
        print("\nTo install SAGA, you may need to:")
        print("1. Install saga-gis package: sudo apt install saga")
        print("2. Enable SAGA provider in QGIS")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        # Cleanup QGIS
        cleanup_qgis(qgs)

if __name__ == "__main__":
    main()

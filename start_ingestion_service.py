#!/usr/bin/env python3
"""
Startup script for AI-Vida Data Ingestion Service
"""

import os
import sys
import subprocess

def main():
    # Get the directory of this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    service_dir = os.path.join(script_dir, 'src', 'backend', 'ingestion-service')
    
    # Change to the service directory
    os.chdir(service_dir)
    
    # Add the service directory to Python path
    sys.path.insert(0, service_dir)
    
    print(f"🚀 Starting AI-Vida Data Ingestion Service from {service_dir}")
    print(f"📍 Service will be available at: http://127.0.0.1:8001")
    print(f"📖 API documentation: http://127.0.0.1:8001/docs")
    print("=" * 60)
    
    try:
        # Import and run the service
        import main
        import uvicorn
        
        uvicorn.run(
            "main:app",
            host="127.0.0.1",
            port=8001,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Service stopped by user")
    except Exception as e:
        print(f"❌ Error starting service: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

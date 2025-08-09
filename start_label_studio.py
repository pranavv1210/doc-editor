#!/usr/bin/env python3
"""
Script to start Label Studio with proper configuration for the Document Editor integration.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_label_studio_installed():
    """Check if Label Studio is installed."""
    try:
        import label_studio
        print("✓ Label Studio is installed")
        return True
    except ImportError:
        print("✗ Label Studio is not installed")
        print("Install it with: pip install label-studio")
        return False

def start_label_studio():
    """Start Label Studio server."""
    print("Starting Label Studio server...")
    
    try:
        # Start Label Studio on port 8080
        process = subprocess.Popen([
            sys.executable, "-m", "label_studio", "start",
            "--port", "8080",
            "--host", "localhost"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✓ Label Studio server started")
        print("  URL: http://localhost:8080")
        print("  Press Ctrl+C to stop the server")
        
        return process
        
    except Exception as e:
        print(f"✗ Failed to start Label Studio: {e}")
        return None

def check_label_studio_running():
    """Check if Label Studio is running."""
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✓ Label Studio is running and accessible")
            return True
        else:
            print(f"✗ Label Studio responded with status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException:
        print("✗ Label Studio is not running or not accessible")
        return False

def main():
    """Main function to start Label Studio."""
    print("=== Label Studio Starter ===\n")
    
    # Check if Label Studio is installed
    if not check_label_studio_installed():
        return
    
    # Check if already running
    if check_label_studio_running():
        print("\nLabel Studio is already running!")
        print("You can access it at: http://localhost:8080")
        return
    
    # Start Label Studio
    process = start_label_studio()
    if not process:
        return
    
    print("\nWaiting for Label Studio to start...")
    
    # Wait for Label Studio to start
    max_wait = 30  # seconds
    for i in range(max_wait):
        time.sleep(1)
        if check_label_studio_running():
            print(f"\n✓ Label Studio started successfully in {i+1} seconds!")
            print("\nYou can now:")
            print("1. Access Label Studio at: http://localhost:8080")
            print("2. Run your Flask app: python app.py")
            print("3. Test the integration: python test_label_studio.py")
            break
    else:
        print(f"\n✗ Label Studio failed to start within {max_wait} seconds")
        print("Check the logs above for any errors")
    
    try:
        # Keep the process running
        process.wait()
    except KeyboardInterrupt:
        print("\n\nStopping Label Studio...")
        process.terminate()
        process.wait()
        print("✓ Label Studio stopped")

if __name__ == "__main__":
    main() 
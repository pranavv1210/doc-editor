#!/usr/bin/env python3
"""
Setup script for Label Studio integration with Document Editor.
"""

import os
import subprocess
import sys
import time
import requests
import webbrowser

def print_header():
    """Print setup header."""
    print("=" * 60)
    print("Label Studio Setup for Document Editor")
    print("=" * 60)
    print()

def check_label_studio_installed():
    """Check if Label Studio is installed."""
    try:
        import label_studio
        print("✓ Label Studio is installed")
        return True
    except ImportError:
        print("✗ Label Studio is not installed")
        print("Installing Label Studio...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "label-studio"])
            print("✓ Label Studio installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install Label Studio")
            return False

def start_label_studio():
    """Start Label Studio server."""
    print("Starting Label Studio server...")
    
    try:
        # Start Label Studio in background
        process = subprocess.Popen([
            sys.executable, "-m", "label_studio", "start",
            "--port", "8080",
            "--host", "localhost"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        print("✓ Label Studio server started")
        print("  URL: http://localhost:8080")
        
        # Wait for server to start
        print("Waiting for server to start...")
        for i in range(30):
            time.sleep(1)
            try:
                response = requests.get("http://localhost:8080", timeout=2)
                if response.status_code == 200:
                    print(f"✓ Server ready in {i+1} seconds!")
                    return process
            except:
                continue
        
        print("✗ Server failed to start within 30 seconds")
        return None
        
    except Exception as e:
        print(f"✗ Failed to start Label Studio: {e}")
        return None

def open_label_studio():
    """Open Label Studio in browser."""
    print("Opening Label Studio in your browser...")
    try:
        webbrowser.open("http://localhost:8080")
        print("✓ Browser opened")
    except Exception as e:
        print(f"✗ Failed to open browser: {e}")
        print("Please manually open: http://localhost:8080")

def get_api_key():
    """Get API key from user."""
    print("\n" + "=" * 40)
    print("SETUP INSTRUCTIONS")
    print("=" * 40)
    print("1. Label Studio should now be open in your browser")
    print("2. Create an account or sign in")
    print("3. Go to Account & Settings")
    print("4. Copy your API key")
    print("5. Enter it below:")
    print()
    
    api_key = input("Enter your Label Studio API key: ").strip()
    
    if api_key:
        # Set environment variable
        os.environ['LABEL_STUDIO_API_KEY'] = api_key
        print("✓ API key set")
        return api_key
    else:
        print("✗ No API key provided")
        return None

def test_integration():
    """Test the Label Studio integration."""
    print("\nTesting Label Studio integration...")
    
    try:
        from label_studio_integration import create_label_studio_integration
        
        ls_integration = create_label_studio_integration()
        
        if ls_integration.test_connection():
            print("✓ Label Studio integration working!")
            return True
        else:
            print("✗ Label Studio integration failed")
            return False
            
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        return False

def create_env_file():
    """Create .env file with API key."""
    api_key = os.getenv('LABEL_STUDIO_API_KEY')
    if api_key:
        try:
            with open('.env', 'w') as f:
                f.write(f'LABEL_STUDIO_API_KEY={api_key}\n')
            print("✓ Created .env file with API key")
        except Exception as e:
            print(f"✗ Failed to create .env file: {e}")

def main():
    """Main setup function."""
    print_header()
    
    # Check if Label Studio is installed
    if not check_label_studio_installed():
        return
    
    # Start Label Studio
    process = start_label_studio()
    if not process:
        return
    
    # Open in browser
    open_label_studio()
    
    # Get API key
    api_key = get_api_key()
    if not api_key:
        print("\nSetup incomplete. Please run this script again.")
        return
    
    # Create .env file
    create_env_file()
    
    # Test integration
    if test_integration():
        print("\n" + "=" * 60)
        print("✓ SETUP COMPLETE!")
        print("=" * 60)
        print("Your Label Studio integration is now ready!")
        print("\nYou can now:")
        print("1. Run your Flask app: python app.py")
        print("2. Test the integration: python test_label_studio.py")
        print("3. Use the Label Studio features in your document editor")
        print("\nThe API key has been saved to the .env file")
        print("You can also set it as an environment variable:")
        print(f"export LABEL_STUDIO_API_KEY={api_key}")
    else:
        print("\n✗ Setup incomplete. Please check the configuration.")
    
    print("\nPress Enter to stop Label Studio...")
    input()
    
    # Stop Label Studio
    print("Stopping Label Studio...")
    process.terminate()
    process.wait()
    print("✓ Label Studio stopped")

if __name__ == "__main__":
    main() 
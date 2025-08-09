import requests
import os

def test_upload():
    url = "http://localhost:5000/upload"
    file_path = "sample.pdf"
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found!")
        return
    
    print(f"Testing upload of {file_path}")
    print(f"File size: {os.path.getsize(file_path)} bytes")
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (file_path, f, 'application/pdf')}
            response = requests.post(url, files=files)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Extracted {len(data.get('content', []))} content items")
        else:
            print("Upload failed!")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_upload() 
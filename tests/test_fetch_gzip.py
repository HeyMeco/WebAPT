import unittest
import requests
import os
import sys
import gzip
import io
from unittest.mock import patch, MagicMock

# Add the parent directory to the sys.path to import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from lib.apt_parser import AptParser

# Define test repositories for easier changes in the future
TEST_REPOSITORIES = [
    {
        "name": "Debian Bullseye",
        "base_url": "http://deb.debian.org/debian",
        "distribution": "bullseye",
        "packages_gz_url": "http://deb.debian.org/debian/dists/bullseye/main/binary-amd64/Packages.gz"
    }
]

class TestFetchGzip(unittest.TestCase):
    """Test the fetch functionality for gzipped Debian repository files"""

    def setUp(self):
        """Set up the test client"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Get the first test repository
        self.test_repo = TEST_REPOSITORIES[0]
        
        # Minimal hardcoded example instead of loading from file
        self.sample_packages = """Package: apt
Priority: required
Version: 2.2.4
Filename: pool/main/a/apt/apt_2.2.4_amd64.deb

Package: libc6
Priority: required
Version: 2.31-13
Filename: pool/main/g/glibc/libc6_2.31-13+deb11u4_amd64.deb
"""
        
        # Create a gzipped version of the Packages file in memory
        self.gzipped_packages = io.BytesIO()
        with gzip.GzipFile(fileobj=self.gzipped_packages, mode='wb') as f:
            f.write(self.sample_packages.encode('utf-8'))
        self.gzipped_content = self.gzipped_packages.getvalue()
        
        # Compression info
        self.original_size = len(self.sample_packages)
        self.compressed_size = len(self.gzipped_content)
        
        print(f"\nPrepared test fixtures:")
        print(f"Original size: {self.original_size} bytes")
        print(f"Compressed size: {self.compressed_size} bytes")
        print(f"Compression ratio: {self.compressed_size/self.original_size:.2f}x")

    @patch('app.requests.get')
    def test_fetch_gzipped_packages_file(self, mock_get):
        """Test fetching a gzipped Packages file from a Debian repository"""
        print("\n\nTesting gzipped Packages file fetching...")
        
        # Mock the response from the requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = self.gzipped_content
        mock_get.return_value = mock_response

        # Call the proxy endpoint with a test URL from the repository array
        test_url = self.test_repo["packages_gz_url"]
        print(f"Fetching gzipped file from URL: {test_url}")
        response = self.app.get(f'/proxy?url={test_url}')

        # Assert that the response is successful
        self.assertEqual(response.status_code, 200, "Should return status code 200")
        print(f"✓ Response successful with status code: {response.status_code}")
        
        # Verify that requests.get was called with the expected URL
        mock_get.assert_called_once_with(
            test_url,
            headers={'User-Agent': 'APT-Repository-Previewer/1.0'},
            timeout=10
        )
        print(f"✓ Request made with correct parameters")
        
        # Verify that the content has been decompressed and contains "Package:"
        decompressed_content = response.data.decode('utf-8')
        decompressed_size = len(decompressed_content)
        
        print(f"\nDecompression results:")
        print(f"Received compressed size: {len(mock_response.content)} bytes")
        print(f"Decompressed size: {decompressed_size} bytes")
        print(f"Original fixture size: {self.original_size} bytes")
        
        # Size comparison should be approximately equal (allowing for line ending differences)
        size_diff = abs(decompressed_size - self.original_size)
        size_diff_percent = (size_diff / self.original_size) * 100
        print(f"Size difference: {size_diff} bytes ({size_diff_percent:.2f}%)")
        
        print("\nVerifying Package entries in decompressed content...")
        package_entries = [line for line in decompressed_content.splitlines() if line.startswith('Package:')]
        package_count = len(package_entries)
        
        print(f"Looking for 'Package:' entries in decompressed content")
        print(f"Found {package_count} package entries")
        if package_count > 0:
            print(f"First package entry found: '{package_entries[0]}'")
            
        self.assertIn("Package:", decompressed_content, "Response should contain Package: entries")
        print("✓ Package entries verification successful")
        
        print("\n✓ Gzipped Packages file fetch test completed successfully")

    @patch('app.requests.get')
    def test_error_handling_corrupt_gzip(self, mock_get):
        """Test handling of errors when fetching a corrupted gzipped file"""
        print("\n\nTesting error handling for corrupted gzip content...")
        
        # Mock the response with corrupted gzip content
        corrupted_content = b'corrupted gzip content'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = corrupted_content
        mock_get.return_value = mock_response

        # Call the proxy endpoint with a test URL from the repository array
        test_url = self.test_repo["packages_gz_url"]
        print(f"Fetching corrupted gzipped file from URL: {test_url}")
        print(f"Corrupted content (first 20 bytes): {corrupted_content[:20]}")
        
        response = self.app.get(f'/proxy?url={test_url}')

        # Assert that the response indicates an error
        self.assertEqual(response.status_code, 500, "Should return status code 500 for corrupted gzip")
        print(f"✓ Error response received with status code: {response.status_code}")
        
        # Verify the error message in the response
        response_json = response.get_json()
        expected_error_text = "Error decompressing"
        
        print(f"Expected error text: '{expected_error_text}'")
        print(f"Actual error: '{response_json.get('error', '')}'")
        
        self.assertIn("error", response_json, "Response should contain an error field")
        self.assertIn(expected_error_text, response_json["error"], f"Response should contain '{expected_error_text}'")
        print("✓ Error message verification successful")
        
        print("\n✓ Corrupted gzip error handling test completed successfully")

if __name__ == '__main__':
    unittest.main() 
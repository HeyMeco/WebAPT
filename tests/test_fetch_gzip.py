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
        "name": "Debian Bookworm",
        "base_url": "http://deb.debian.org/debian",
        "distribution": "bookworm",
        "packages_gz_url": "http://deb.debian.org/debian/dists/bookworm/main/binary-amd64/Packages.gz"
    },
    {
        "name": "Ubuntu Archive",
        "base_url": "https://archive.ubuntu.com/ubuntu",
        "distribution": "noble",
        "packages_gz_url": "https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz"
    }
]

class TestFetchGzip(unittest.TestCase):
    """Test the fetch functionality for gzipped Debian repository files"""

    def setUp(self):
        """Set up the test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_fetch_gzipped_packages_file(self):
        """Test fetching a gzipped Packages file from repositories using real requests"""
        print("\n\nTesting gzipped Packages file fetching...")
        
        for repo in TEST_REPOSITORIES:
            with self.subTest(repository=repo["name"]):
                print(f"\nTesting repository: {repo['name']}")
                
                # Call the proxy endpoint with a test URL from the repository array
                test_url = repo["packages_gz_url"]
                print(f"Fetching gzipped file from URL: {test_url}")
                response = self.app.get(f'/proxy?url={test_url}')

                # Assert that the response is successful
                self.assertEqual(response.status_code, 200, f"Should return status code 200 for {repo['name']}")
                print(f"✓ Response successful with status code: {response.status_code}")
                
                # Verify that the content has been decompressed and is valid
                decompressed_content = response.data.decode('utf-8')
                
                # Verify decompression was successful by checking content length
                self.assertGreater(len(decompressed_content), 100, 
                                  f"Decompressed content for {repo['name']} is too short")
                print(f"Decompressed content size: {len(decompressed_content)} bytes")
                
                # Verify that we can parse the Packages content
                packages = AptParser.parse_packages(decompressed_content)
                package_count = len(packages)
                
                # Ensure we got packages
                self.assertGreater(package_count, 0, f"Should have parsed packages from {repo['name']}")
                print(f"Parsed {package_count} packages from {repo['name']}")
                
                # Print some stats about the packages
                print("\nPackage statistics:")
                if package_count > 0:
                    # Sample a few packages
                    sample_size = min(3, package_count)
                    print(f"Showing first {sample_size} packages from total of {package_count}:")
                    for i, package in enumerate(packages[:sample_size]):
                        print(f"  {i+1}. {package.get('name', 'Unknown')} - {package.get('version', 'Unknown version')}")
                
                # Verify required fields in packages
                required_fields = ['name', 'version', 'filename']
                for field in required_fields:
                    for i, package in enumerate(packages[:10]):  # Check first 10 packages
                        self.assertIn(field, package, f"Package {i+1} missing required field: {field}")
                
                print(f"✓ All required fields present in package entries")
                print(f"\n✓ Gzipped Packages file fetch and validation completed successfully for {repo['name']}")

    def test_error_handling_corrupt_gzip(self):
        """Test handling of errors when fetching a corrupted gzipped file"""
        print("\n\nTesting error handling for corrupted gzip content...")
        
        # For error testing, we'll use a non-gzip URL but request it as if it were .gz
        # The Release file isn't gzipped, so trying to decompress it should fail
        for repo in TEST_REPOSITORIES:
            with self.subTest(repository=repo["name"]):
                print(f"\nTesting repository: {repo['name']}")
                
                # Create a URL to a non-gzipped file but with .gz extension
                # This should cause a decompression error
                corrupt_url = repo["packages_gz_url"].replace("Packages.gz", "Release.gz")
                print(f"Fetching corrupted gzipped file from URL: {corrupt_url}")
                
                response = self.app.get(f'/proxy?url={corrupt_url}')

                # The proxy should return an error status
                self.assertIn(response.status_code, [404, 500], 
                            f"Should return error status code for {repo['name']}")
                print(f"✓ Error response received with status code: {response.status_code}")
                
                # If we get a 500 error (decompression error), verify the error message
                if response.status_code == 500:
                    response_json = response.get_json()
                    expected_error_text = "Error decompressing"
                    
                    print(f"Error message: '{response_json.get('error', '')}'")
                    
                    self.assertIn("error", response_json, "Response should contain an error field")
                    self.assertIn(expected_error_text, response_json.get("error", ""), 
                                f"Response should contain '{expected_error_text}'")
                    print("✓ Error message verification successful")
                else:
                    print("✓ Expected 404 error for non-existent file")
                
                print(f"\n✓ Error handling test completed successfully for {repo['name']}")

if __name__ == '__main__':
    unittest.main() 
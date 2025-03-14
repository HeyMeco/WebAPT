import unittest
import requests
import os
import sys
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
        "release_url": "http://deb.debian.org/debian/dists/bullseye/Release",
        "packages_url": "http://deb.debian.org/debian/dists/bullseye/main/binary-amd64/Packages.gz",
        "expected_origin": "Debian",
        "expected_suite": "oldstable"  # Bullseye is now oldstable
    },
    {
        "name": "Ubuntu Archive",
        "base_url": "https://archive.ubuntu.com/ubuntu",
        "distribution": "noble",
        "release_url": "https://archive.ubuntu.com/ubuntu/dists/noble/Release",
        "packages_url": "https://archive.ubuntu.com/ubuntu/dists/noble/main/binary-amd64/Packages.gz",
        "expected_origin": "Ubuntu",
        "expected_suite": "noble"
    }
]

class TestFetch(unittest.TestCase):
    """Test the fetch functionality for Debian repositories"""

    def setUp(self):
        """Set up the test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_proxy_endpoint_exists(self):
        """Test that the proxy endpoint exists"""
        response = self.app.get('/proxy')
        self.assertNotEqual(response.status_code, 404, "Proxy endpoint should exist")
        print(f"\n✓ Proxy endpoint exists with status code {response.status_code}")

    def test_fetch_release_file(self):
        """Test fetching a Release file from repositories using real requests"""
        print("\n\nTesting Release file fetching...")
        
        for repo in TEST_REPOSITORIES:
            with self.subTest(repository=repo["name"]):
                print(f"\nTesting repository: {repo['name']}")
                
                # Call the proxy endpoint with the test URL from the repository
                test_url = repo["release_url"]
                print(f"Fetching from URL: {test_url}")
                response = self.app.get(f'/proxy?url={test_url}')

                # Assert that the response is successful
                self.assertEqual(response.status_code, 200, f"Should return status code 200 for {repo['name']}")
                print(f"✓ Response successful with status code: {response.status_code}")
                
                # Decode response text
                response_text = response.data.decode('utf-8')
                
                # Verify Release file structure by parsing it
                parsed_release = AptParser.parse_release_file(response_text)
                print("\nValidating repository metadata...")
                
                # Check essential fields
                self.assertIn('Origin', parsed_release, f"Release file for {repo['name']} should contain Origin")
                self.assertIn('Suite', parsed_release, f"Release file for {repo['name']} should contain Suite")
                self.assertIn('Codename', parsed_release, f"Release file for {repo['name']} should contain Codename")
                self.assertIn('Architectures', parsed_release, f"Release file for {repo['name']} should contain Architectures")
                self.assertIn('Components', parsed_release, f"Release file for {repo['name']} should contain Components")
                
                # Print and verify values against expected ones
                print(f"Origin: {parsed_release['Origin']}")
                print(f"Suite: {parsed_release['Suite']}")
                print(f"Codename: {parsed_release['Codename']}")
                print(f"Architectures: {parsed_release['Architectures']}")
                print(f"Components: {parsed_release['Components']}")
                
                # Verify expected values if provided
                if "expected_origin" in repo:
                    expected_origin = repo["expected_origin"]
                    self.assertEqual(parsed_release['Origin'], expected_origin, 
                                   f"Unexpected Origin: got '{parsed_release['Origin']}', expected '{expected_origin}'")
                    print(f"✓ Origin verification successful for {repo['name']}")
                    
                if "expected_suite" in repo:
                    expected_suite = repo["expected_suite"]
                    self.assertEqual(parsed_release['Suite'], expected_suite, 
                                   f"Unexpected Suite: got '{parsed_release['Suite']}', expected '{expected_suite}'")
                    print(f"✓ Suite verification successful for {repo['name']}")
                
                print(f"\n✓ Release file fetch and validation completed successfully for {repo['name']}")

    def test_fetch_packages_file(self):
        """Test fetching a Packages file from repositories using real requests"""
        print("\n\nTesting Packages file fetching...")
        
        for repo in TEST_REPOSITORIES:
            with self.subTest(repository=repo["name"]):
                print(f"\nTesting repository: {repo['name']}")
                
                # Call the proxy endpoint with the test URL from the repository
                test_url = repo["packages_url"]
                print(f"Fetching from URL: {test_url}")
                response = self.app.get(f'/proxy?url={test_url}')

                # Assert that the response is successful
                self.assertEqual(response.status_code, 200, f"Should return status code 200 for {repo['name']}")
                print(f"✓ Response successful with status code: {response.status_code}")
                
                # Decode response text
                response_text = response.data.decode('utf-8')
                
                # Verify that we can parse the Packages content
                packages = AptParser.parse_packages(response_text)
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
                print(f"\n✓ Packages file fetch and validation completed successfully for {repo['name']}")

    def test_error_handling(self):
        """Test handling of errors when fetching from repositories"""
        print("\n\nTesting error handling...")
        
        # Use a non-existent URL to test error handling
        test_url = "http://invalid-repo.example.com/debian/dists/bullseye/Release"
        print(f"Fetching from invalid URL: {test_url}")
        response = self.app.get(f'/proxy?url={test_url}')

        # Assert that the response indicates an error
        self.assertEqual(response.status_code, 500, "Should return status code 500 for connection errors")
        print(f"✓ Error response received with status code: {response.status_code}")
        
        # Verify the error message in the response
        response_json = response.get_json()
        self.assertIn("error", response_json, "Response should contain an error field")
        print(f"Error message: '{response_json.get('error', '')}'")
        print("✓ Error message verification successful")
        
        print("\n✓ Error handling test completed successfully")
        
    def test_integration_fetch_flow(self):
        """
        Test the full flow of fetching and parsing repositories
        First getting the Release file, then getting Packages for each component/arch
        """
        print("\n\nTesting full repository fetch flow...")
        
        for repo in TEST_REPOSITORIES:
            with self.subTest(repository=repo["name"]):
                print(f"\nTesting repository: {repo['name']}")
                
                # Step 1: Fetch the Release file
                print("\nStep 1: Fetching Release file...")
                release_url = repo["release_url"]
                response = self.app.get(f'/proxy?url={release_url}')
                self.assertEqual(response.status_code, 200, f"Should return status code 200 for {repo['name']} Release")
                print(f"✓ Release fetch successful with status code: {response.status_code}")
                
                # Parse the Release file to get components and architectures
                response_text = response.data.decode('utf-8')
                release_data = AptParser.parse_release_file(response_text)
                
                # Verify essential Release file information
                print(f"Repository: {release_data.get('Origin', 'Unknown')} {release_data.get('Suite', 'Unknown')}")
                print(f"Codename: {release_data.get('Codename', 'Unknown')}")
                
                # Verify existence of required fields for URL building
                self.assertIn('Components', release_data, "Release data should contain Components")
                self.assertIn('Architectures', release_data, "Release data should contain Architectures")
                self.assertIn('Codename', release_data, "Release data should contain Codename")
                
                print(f"Components: {release_data['Components']}")
                print(f"Architectures: {release_data['Architectures']}")
                
                # Step 2: Fetch Packages file for main/amd64
                print("\nStep 2: Fetching Packages file...")
                component = release_data['Components'][0]  # Just use the first component
                
                # Make sure we use a valid architecture
                valid_archs = ['amd64', 'arm64', 'i386']
                arch = next((a for a in valid_archs if a in release_data['Architectures']), 'amd64')
                    
                codename = release_data['Codename']
                
                print(f"Using Component: {component}")
                print(f"Using Architecture: {arch}")
                print(f"Using Codename: {codename}")
                
                packages_url = AptParser.build_packages_url(repo["base_url"], codename, component, arch) + ".gz"
                print(f"Built Packages URL: {packages_url}")
                
                response = self.app.get(f'/proxy?url={packages_url}')
                self.assertEqual(response.status_code, 200, f"Should return status code 200 for {repo['name']} Packages")
                print(f"✓ Packages fetch successful with status code: {response.status_code}")
                
                # Parse the Packages file to get package information
                response_text = response.data.decode('utf-8')
                packages = AptParser.parse_packages(response_text)
                
                # Verify we got packages
                package_count = len(packages)
                self.assertGreater(package_count, 0, f"Should have parsed packages from {repo['name']}")
                print(f"Parsed {package_count} packages from {repo['name']}")
                
                # Sample a few packages
                sample_size = min(3, package_count)
                print(f"\nShowing sample of {sample_size} packages:")
                for i, package in enumerate(packages[:sample_size]):
                    print(f"  {i+1}. {package.get('name', 'Unknown')} - {package.get('version', 'Unknown version')}")
                
                print(f"\n✓ Full repository fetch flow completed successfully for {repo['name']}")

if __name__ == '__main__':
    unittest.main() 
import unittest
import requests
import os
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the sys.path to import the app module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from lib.apt_parser import AptParser

class TestFetch(unittest.TestCase):
    """Test the fetch functionality for Debian repositories"""

    def setUp(self):
        """Set up the test client"""
        self.app = app.test_client()
        self.app.testing = True
        
        # Minimal hardcoded examples instead of loading from files
        self.sample_release = """Origin: Debian
Suite: stable
Codename: bullseye
Architectures: amd64 arm64
Components: main contrib
Description: Debian 11 Released
"""
        
        self.sample_packages = """Package: apt
Priority: required
Version: 2.2.4
Filename: pool/main/a/apt/apt_2.2.4_amd64.deb

Package: libc6
Priority: required
Version: 2.31-13
Filename: pool/main/g/glibc/libc6_2.31-13+deb11u4_amd64.deb
"""
        
        # Define expected values
        self.expected_origin = "Debian"
        self.expected_suite = "stable"

    def test_proxy_endpoint_exists(self):
        """Test that the proxy endpoint exists"""
        response = self.app.get('/proxy')
        self.assertNotEqual(response.status_code, 404, "Proxy endpoint should exist")
        print(f"\n✓ Proxy endpoint exists with status code {response.status_code}")

    @patch('app.requests.get')
    def test_fetch_release_file(self, mock_get):
        """Test fetching a Release file from a Debian repository"""
        print("\n\nTesting Release file fetching...")
        
        # Mock the response from the requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.sample_release
        mock_get.return_value = mock_response

        # Call the proxy endpoint with a test URL
        test_url = "http://deb.debian.org/debian/dists/bullseye/Release"
        print(f"Fetching from URL: {test_url}")
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
        
        # Decode response text
        response_text = response.data.decode('utf-8')
        
        # Only verify Origin and Suite in the response
        print("\nVerifying Origin and Suite in raw response...")
        origin_line = next((line for line in response_text.splitlines() if line.startswith('Origin:')), None)
        suite_line = next((line for line in response_text.splitlines() if line.startswith('Suite:')), None)
        
        print(f"Expected Origin: '{self.expected_origin}'")
        print(f"Found in response: '{origin_line}'")
        self.assertIn(f"Origin: {self.expected_origin}", response_text, 
                     f"Response should contain 'Origin: {self.expected_origin}'")
        print("✓ Origin verification successful")
        
        print(f"Expected Suite: '{self.expected_suite}'")
        print(f"Found in response: '{suite_line}'")
        self.assertIn(f"Suite: {self.expected_suite}", response_text, 
                     f"Response should contain 'Suite: {self.expected_suite}'")
        print("✓ Suite verification successful")
        
        # Test that we can parse the response using AptParser
        print("\nVerifying Origin and Suite in parsed response...")
        parsed_release = AptParser.parse_release_file(response_text)
        
        print(f"Expected Origin: '{self.expected_origin}'")
        print(f"Parsed Origin: '{parsed_release['Origin']}'")
        self.assertEqual(parsed_release['Origin'], self.expected_origin, 
                        f"Parsed Origin should be '{self.expected_origin}'")
        print("✓ Parsed Origin verification successful")
        
        print(f"Expected Suite: '{self.expected_suite}'")
        print(f"Parsed Suite: '{parsed_release['Suite']}'")
        self.assertEqual(parsed_release['Suite'], self.expected_suite, 
                        f"Parsed Suite should be '{self.expected_suite}'")
        print("✓ Parsed Suite verification successful")
        
        print("\n✓ Release file fetch test completed successfully")

    @patch('app.requests.get')
    def test_fetch_packages_file(self, mock_get):
        """Test fetching a Packages file from a Debian repository"""
        print("\n\nTesting Packages file fetching...")
        
        # Mock the response from the requests.get call
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = self.sample_packages
        mock_get.return_value = mock_response

        # Call the proxy endpoint with a test URL
        test_url = "http://deb.debian.org/debian/dists/bullseye/main/binary-amd64/Packages"
        print(f"Fetching from URL: {test_url}")
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
        
        # Only verify that "Package:" exists in the content
        response_text = response.data.decode('utf-8')
        
        print("\nVerifying Package entries in response...")
        package_entries = [line for line in response_text.splitlines() if line.startswith('Package:')]
        package_count = len(package_entries)
        
        print(f"Looking for 'Package:' entries in response")
        print(f"Found {package_count} package entries")
        if package_count > 0:
            print(f"First package entry found: '{package_entries[0]}'")
            
        self.assertIn("Package:", response_text, "Response should contain Package: entries")
        print("✓ Package entries verification successful")
        
        print("\n✓ Packages file fetch test completed successfully")

    @patch('app.requests.get')
    def test_error_handling(self, mock_get):
        """Test handling of errors when fetching from a repository"""
        print("\n\nTesting error handling...")
        
        # Mock the response to raise an exception
        error_message = "Connection error"
        mock_get.side_effect = requests.exceptions.RequestException(error_message)

        # Call the proxy endpoint with a test URL
        test_url = "http://invalid-repo.example.com/debian/dists/bullseye/Release"
        print(f"Fetching from invalid URL: {test_url}")
        response = self.app.get(f'/proxy?url={test_url}')

        # Assert that the response indicates an error
        self.assertEqual(response.status_code, 500, "Should return status code 500 for connection errors")
        print(f"✓ Error response received with status code: {response.status_code}")
        
        # Verify the error message in the response
        response_json = response.get_json()
        print(f"Expected error message contains: '{error_message}'")
        print(f"Actual error message: '{response_json.get('error', '')}'")
        
        self.assertIn("error", response_json, "Response should contain an error field")
        self.assertIn(error_message, response_json["error"], f"Response should contain '{error_message}'")
        print("✓ Error message verification successful")
        
        print("\n✓ Error handling test completed successfully")
        
    @patch('app.requests.get')
    def test_integration_fetch_flow(self, mock_get):
        """
        Test the full flow of fetching and parsing a Debian repository
        First getting the Release file, then getting Packages for each component/arch
        """
        print("\n\nTesting full repository fetch flow...")
        
        # Mock for Release file
        release_response = MagicMock()
        release_response.status_code = 200
        release_response.text = self.sample_release
        
        # Mock for Packages file
        packages_response = MagicMock()
        packages_response.status_code = 200
        packages_response.text = self.sample_packages
        
        # Configure mock to return different responses based on URL
        def side_effect(url, **kwargs):
            if '/Release' in url:
                print(f"Mock returning Release file for URL: {url}")
                return release_response
            if '/Packages' in url:
                print(f"Mock returning Packages file for URL: {url}")
                return packages_response
            print(f"Mock returning 404 for URL: {url}")
            return MagicMock(status_code=404, text="Not Found")
            
        mock_get.side_effect = side_effect
        
        # Step 1: Fetch the Release file
        print("\nStep 1: Fetching Release file...")
        release_url = "http://deb.debian.org/debian/dists/bullseye/Release"
        response = self.app.get(f'/proxy?url={release_url}')
        self.assertEqual(response.status_code, 200)
        print(f"✓ Release fetch successful with status code: {response.status_code}")
        
        # Parse the Release file to get components and architectures
        response_text = response.data.decode('utf-8')
        
        # Verify Origin and Suite in the Release file
        print("\nVerifying Origin and Suite in Release file...")
        origin_line = next((line for line in response_text.splitlines() if line.startswith('Origin:')), None)
        suite_line = next((line for line in response_text.splitlines() if line.startswith('Suite:')), None)
        
        print(f"Expected Origin: '{self.expected_origin}'")
        print(f"Found in response: '{origin_line}'")
        self.assertIn(f"Origin: {self.expected_origin}", response_text)
        print("✓ Origin verification successful")
        
        print(f"Expected Suite: '{self.expected_suite}'")
        print(f"Found in response: '{suite_line}'")
        self.assertIn(f"Suite: {self.expected_suite}", response_text)
        print("✓ Suite verification successful")
        
        release_data = AptParser.parse_release_file(response_text)
        
        # Only validate Origin and Suite
        print("\nVerifying parsed Origin and Suite...")
        print(f"Expected Origin: '{self.expected_origin}'")
        print(f"Parsed Origin: '{release_data['Origin']}'")
        self.assertEqual(release_data['Origin'], self.expected_origin)
        print("✓ Parsed Origin verification successful")
        
        print(f"Expected Suite: '{self.expected_suite}'")
        print(f"Parsed Suite: '{release_data['Suite']}'")
        self.assertEqual(release_data['Suite'], self.expected_suite)
        print("✓ Parsed Suite verification successful")
        
        # Still need these for building the URL, but don't validate their values
        print("\nVerifying existence of required fields for URL building...")
        self.assertTrue('Components' in release_data, "Release data should contain Components")
        print(f"✓ Components found: {release_data['Components']}")
        
        self.assertTrue('Architectures' in release_data, "Release data should contain Architectures")
        print(f"✓ Architectures found: {release_data['Architectures']}")
        
        self.assertTrue('Codename' in release_data, "Release data should contain Codename")
        print(f"✓ Codename found: {release_data['Codename']}")
        
        # Step 2: Fetch Packages file for main/amd64
        print("\nStep 2: Fetching Packages file...")
        component = release_data['Components'][0]  # Just use the first component
        arch = release_data['Architectures'][0]     # Just use the first architecture
        codename = release_data['Codename']
        
        print(f"Using Component: {component}")
        print(f"Using Architecture: {arch}")
        print(f"Using Codename: {codename}")
        
        packages_url = AptParser.build_packages_url("http://deb.debian.org/debian", codename, component, arch)
        print(f"Built Packages URL: {packages_url}")
        
        response = self.app.get(f'/proxy?url={packages_url}')
        self.assertEqual(response.status_code, 200)
        print(f"✓ Packages fetch successful with status code: {response.status_code}")
        
        # Verify that "Package:" exists in the Packages file
        print("\nVerifying Package entries in Packages file...")
        response_text = response.data.decode('utf-8')
        package_entries = [line for line in response_text.splitlines() if line.startswith('Package:')]
        package_count = len(package_entries)
        
        print(f"Looking for 'Package:' entries in response")
        print(f"Found {package_count} package entries")
        if package_count > 0:
            print(f"First package entry found: '{package_entries[0]}'")
            
        self.assertIn("Package:", response_text, "Response should contain Package: entries")
        print("✓ Package entries verification successful")
        
        print("\n✓ Full repository fetch flow test completed successfully")

if __name__ == '__main__':
    unittest.main() 
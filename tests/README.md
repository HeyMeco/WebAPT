# APT Repository Viewer Tests

This directory contains tests for the APT Repository Viewer application.

## Running Tests

To run all tests:

```bash
# From the project root directory
uv run python -m unittest discover tests
```

To run a specific test file:

```bash
# From the project root directory
uv run python -m unittest tests/test_fetch.py
```

## Test Descriptions

### `test_fetch.py`

Tests the fetch functionality for Debian repositories. These tests verify that:

1. The `/proxy` endpoint exists and can be accessed
2. The application can fetch Release files from Debian repositories (validating only Origin and Suite fields)
3. The application can fetch Packages files from Debian repositories (validating only that the response contains "Package:")
4. The application handles errors properly when fetching from repositories
5. The complete fetch flow works (first fetching Release then Packages files)

The tests focus only on validating that:
- We can fetch the data
- Release files contain the expected Origin and Suite fields
- Packages files contain "Package:" entries

### `test_fetch_gzip.py`

Tests the fetch functionality for gzipped Debian repository files. These tests verify that:

1. The application can fetch and decompress gzipped Packages files (validating only that the decompressed content contains "Package:")
2. The application handles errors properly when dealing with corrupted gzip content

These tests use mock objects to simulate responses from external repositories, so they don't depend on external services being available.

## Self-Contained Tests

The tests are designed to be completely self-contained with no external dependencies:

- All test fixtures (sample Release and Packages data) are hardcoded within the test files
- Minimal examples are used that contain only the fields necessary for testing
- For Release files: Contains Origin, Suite, Codename, Architectures, and Components
- For Packages files: Contains basic Package entries with name, version, and filename

This approach ensures the tests are focused on validating only the specific functionality we care about (the fetch ability) without being dependent on external files.

## Verbose Output

The tests are designed to be human-readable with detailed output showing:

1. For Release files:
   - The expected Origin ("Debian") and Suite ("stable") values
   - The actual values found in the response
   - Success/failure status for each validation

2. For Packages files:
   - Number of package entries found
   - Sample of the first package entry found
   - Success/failure status for "Package:" existence check

3. For gzipped files:
   - Original and compressed sizes
   - Compression ratio
   - Decompression success details
   - Package entries found in decompressed content

This verbose output makes it easy to understand what's being tested and whether the tests are passing for the right reasons. Run the tests with the commands above to see the detailed output. 
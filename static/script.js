// WebAPT - Client Side JavaScript
document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const repoUrlInput = document.getElementById('repoUrl');
    const loadButton = document.getElementById('loadButton');
    const appTitle = document.querySelector('h1');
    const releaseInfoDiv = document.getElementById('releaseInfo');
    const infoGridDiv = document.getElementById('infoGrid');
    const archSelect = document.getElementById('archSelect');
    const componentSelect = document.getElementById('componentSelect');
    const distSelect = document.getElementById('distSelect');
    const packagesUrlDiv = document.getElementById('packagesUrl');
    const errorMessageDiv = document.getElementById('errorMessage');
    const packageCountDiv = document.getElementById('packageCount');
    const tableContainerDiv = document.getElementById('tableContainer');
    const packagesTable = document.getElementById('packagesTable');
    const searchQueryInput = document.getElementById('searchQuery');
    const firstPageBtn = document.getElementById('firstPageBtn');
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const lastPageBtn = document.getElementById('lastPageBtn');
    const pageInput = document.getElementById('pageInput');
    const totalPagesSpan = document.getElementById('totalPages');

    // State
    let releaseInfo = null;
    let packagesUrl = '';
    let packages = [];
    let currentPage = 1;
    let pageSize = 20;
    let searchQuery = '';
    let sortField = 'name';
    let sortDirection = 'asc';
    let repoBaseUrl = '';
    let availableDists = [];
    let defaultDist = 'stable';

    // Proxy URL
    const PROXY_URL = '/proxy?url=';

    // Event Listeners
    repoUrlInput.addEventListener('keyup', (e) => {
        if (e.key === 'Enter') {
            fetchRelease();
        }
    });

    loadButton.addEventListener('click', fetchRelease);
    
    // Add click handler to the app title to reset the application
    appTitle.addEventListener('click', () => {
        resetState();
        repoUrlInput.value = '';
    });
    
    // Add CSS class for clickable title instead of setting the style directly
    appTitle.classList.add('clickable-title');

    archSelect.addEventListener('change', updatePackagesUrl);
    componentSelect.addEventListener('change', updatePackagesUrl);
    distSelect.addEventListener('change', handleDistChange);
    distSelect.addEventListener('change', updatePackagesUrl);

    searchQueryInput.addEventListener('input', (e) => {
        searchQuery = e.target.value.toLowerCase();
        currentPage = 1;
        pageInput.value = 1;
        renderTable();
    });

    firstPageBtn.addEventListener('click', () => {
        currentPage = 1;
        pageInput.value = 1;
        renderTable();
    });

    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            pageInput.value = currentPage;
            renderTable();
        }
    });

    nextPageBtn.addEventListener('click', () => {
        if (currentPage < getTotalPages()) {
            currentPage++;
            pageInput.value = currentPage;
            renderTable();
        }
    });

    lastPageBtn.addEventListener('click', () => {
        currentPage = getTotalPages();
        pageInput.value = currentPage;
        renderTable();
    });

    pageInput.addEventListener('change', () => {
        const value = parseInt(pageInput.value);
        if (!isNaN(value) && value >= 1 && value <= getTotalPages()) {
            currentPage = value;
            renderTable();
        } else {
            pageInput.value = currentPage;
        }
    });

    // Functions
    async function fetchRelease() {
        let repoUrl = repoUrlInput.value.trim();
        
        // Use default URL if input is empty
        if (!repoUrl) {
            repoUrl = 'https://apt.armbian.com';
            repoUrlInput.value = repoUrl;
        }

        try {
            // Reset all state and selections before loading a new repository
            resetState();
            
            showLoading(true);
            clearError();
            hidePackagesInfo();

            // Extract the base URL (domain + path up to /dists/)
            const cleanBaseUrl = repoUrl.replace(/\/$/, '');
            if (cleanBaseUrl.includes('/dists/')) {
                repoBaseUrl = cleanBaseUrl.split('/dists/')[0];
            } else {
                repoBaseUrl = cleanBaseUrl;
            }

            // Try to extract the distribution from the URL
            let initialDist = defaultDist;
            if (cleanBaseUrl.includes('/dists/')) {
                const [_, distsPath] = cleanBaseUrl.split('/dists/');
                if (distsPath && distsPath.trim() !== '') {
                    initialDist = distsPath.split('/')[0];
                }
            }

            // Build the Release file URL - handle different URL patterns
            let releaseUrl;
            if (cleanBaseUrl.includes('/dists/')) {
                // Extract the base part and the path after dists/
                const [basePart, distsPath] = cleanBaseUrl.split('/dists/');
                
                if (distsPath.includes('/')) {
                    // URL already includes a specific path after dists/
                    releaseUrl = `${cleanBaseUrl}/Release`;
                } else if (distsPath && distsPath.trim() !== '') {
                    // URL has something after dists/ but no additional path
                    releaseUrl = `${cleanBaseUrl}/Release`;  
                } else {
                    // URL just ends with dists/
                    releaseUrl = `${basePart}/dists/${initialDist}/Release`;
                }
            } else {
                releaseUrl = `${cleanBaseUrl}/dists/${initialDist}/Release`;
            }
            
            // Fetch the Release file through the proxy
            const response = await fetch(PROXY_URL + encodeURIComponent(releaseUrl));
            const releaseContent = await response.text();

            if (response.status !== 200) {
                throw new Error(`Failed to fetch Release file: ${response.statusText}`);
            }

            // Parse the Release file content
            releaseInfo = parseReleaseFile(releaseContent);
            
            // Check for Suite and Codename to determine available distributions
            availableDists = [];
            if (releaseInfo.Suite) availableDists.push(releaseInfo.Suite);
            if (releaseInfo.Codename && releaseInfo.Codename !== releaseInfo.Suite) availableDists.push(releaseInfo.Codename);
            
            // Fetch dists directory to discover available distributions
            try {
                await fetchAvailableDists();
            } catch (e) {
                console.warn("Could not fetch available distributions:", e);
            }
            
            // Add the initial dist if not already in the list
            if (!availableDists.includes(initialDist)) {
                availableDists.push(initialDist);
            }
            
            // Show release info
            showReleaseInfo();
        } catch (error) {
            showError(`Error loading repository: ${error.message}`);
        } finally {
            showLoading(false);
        }
    }

    async function fetchPackages() {
        if (!packagesUrl) {
            showError('Invalid packages URL');
            return;
        }

        try {
            showLoading(true);
            clearError();

            // Fetch the Packages file through the proxy
            const response = await fetch(PROXY_URL + encodeURIComponent(packagesUrl));
            const packagesContent = await response.text();

            if (response.status !== 200) {
                throw new Error(`Failed to fetch Packages file: ${response.statusText}`);
            }

            // Parse the Packages file content
            packages = parsePackages(packagesContent);
            
            // Show packages table
            showPackagesTable();
        } catch (error) {
            showError(`Error loading packages: ${error.message}`);
        } finally {
            showLoading(false);
        }
    }

    function updatePackagesUrl() {
        const arch = archSelect.value;
        const component = componentSelect.value;
        const dist = distSelect.value;
        
        if (!arch || !component || !dist || !releaseInfo) {
            packagesUrl = '';
            packagesUrlDiv.style.display = 'none';
            return;
        }

        // Build the Packages URL
        packagesUrl = buildPackagesUrl(
            repoUrlInput.value.trim(),
            dist,
            component,
            arch
        );

        // Display the URL
        packagesUrlDiv.textContent = `Packages URL: ${packagesUrl}`;
        packagesUrlDiv.style.display = 'block';

        // Fetch packages
        fetchPackages();
    }

    async function fetchAvailableDists() {
        if (!repoBaseUrl) return;
        
        // Try to fetch the /dists/ directory to discover available distributions
        // This may not work on all repositories as they might not allow directory listings
        try {
            const distsUrl = `${repoBaseUrl}/dists/`;
            const response = await fetch(PROXY_URL + encodeURIComponent(distsUrl));
            const content = await response.text();
            
            // Simple regex to find directory names
            // This is a basic approach and might not work for all server configurations
            const dirRegex = /<a[^>]*href="([^"\/]+)\/"[^>]*>/g;
            let match;
            
            while ((match = dirRegex.exec(content)) !== null) {
                const dist = match[1];
                if (!availableDists.includes(dist) && dist !== '.' && dist !== '..') {
                    availableDists.push(dist);
                }
            }
        } catch (error) {
            console.warn("Failed to fetch distributions from directory listing", error);
        }
    }

    async function handleDistChange() {
        const dist = distSelect.value;
        
        if (!dist || !repoBaseUrl) {
            return;
        }

        try {
            showLoading(true);
            clearError();
            
            // Reset package-related UI elements
            packagesUrl = '';
            packagesUrlDiv.style.display = 'none';
            packageCountDiv.style.display = 'none';
            tableContainerDiv.style.display = 'none';
            
            // Reset architecture and component selections before fetching new data
            archSelect.innerHTML = '<option value="">Select Architecture</option>';
            componentSelect.innerHTML = '<option value="">Select Component</option>';
            
            // Build the Release file URL for the selected distribution
            const releaseUrl = `${repoBaseUrl}/dists/${dist}/Release`;
            
            // Fetch the Release file through the proxy
            const response = await fetch(PROXY_URL + encodeURIComponent(releaseUrl));
            const releaseContent = await response.text();

            if (response.status !== 200) {
                throw new Error(`Failed to fetch Release file for ${dist}: ${response.statusText}`);
            }

            // Parse the Release file content
            releaseInfo = parseReleaseFile(releaseContent);
            
            // Populate architecture dropdown
            if (releaseInfo.Architectures) {
                releaseInfo.Architectures.forEach(arch => {
                    const option = document.createElement('option');
                    option.value = arch;
                    option.textContent = arch;
                    archSelect.appendChild(option);
                });
            }
            
            // Populate component dropdown
            if (releaseInfo.Components) {
                releaseInfo.Components.forEach(component => {
                    const option = document.createElement('option');
                    option.value = component;
                    option.textContent = component;
                    componentSelect.appendChild(option);
                });
            }
            
            // Update info grid with the new release info
            updateReleaseInfoGrid();
            
        } catch (error) {
            showError(`Error loading distribution: ${error.message}`);
        } finally {
            showLoading(false);
        }
    }
    
    function updateReleaseInfoGrid() {
        if (!releaseInfo) return;

        // Clear the info grid
        infoGridDiv.innerHTML = '';

        // Display important fields
        const importantFields = ['Origin', 'Label', 'Suite', 'Codename', 'Version', 'Date', 'Valid-Until', 'NotAutomatic', 'ButAutomaticUpgrades'];
        
        importantFields.forEach(field => {
            if (releaseInfo[field]) {
                const div = document.createElement('div');
                const strong = document.createElement('strong');
                strong.textContent = field + ': ';
                const span = document.createElement('span');
                span.textContent = releaseInfo[field];
                div.appendChild(strong);
                div.appendChild(span);
                infoGridDiv.appendChild(div);
            }
        });
    }
    
    function showReleaseInfo() {
        if (!releaseInfo) return;

        // Update info grid
        updateReleaseInfoGrid();

        // Populate architecture dropdown
        archSelect.innerHTML = '<option value="">Select Architecture</option>';
        if (releaseInfo.Architectures) {
            releaseInfo.Architectures.forEach(arch => {
                const option = document.createElement('option');
                option.value = arch;
                option.textContent = arch;
                archSelect.appendChild(option);
            });
        }

        // Populate component dropdown
        componentSelect.innerHTML = '<option value="">Select Component</option>';
        if (releaseInfo.Components) {
            releaseInfo.Components.forEach(component => {
                const option = document.createElement('option');
                option.value = component;
                option.textContent = component;
                componentSelect.appendChild(option);
            });
        }
        
        // Populate distribution dropdown
        distSelect.innerHTML = '<option value="">Select Distribution</option>';
        availableDists.sort().forEach(dist => {
            const option = document.createElement('option');
            option.value = dist;
            option.textContent = dist;
            // Set the active distribution based on Codename or selected value
            if ((releaseInfo.Codename && dist === releaseInfo.Codename) || 
                 distSelect.value === dist) {
                option.selected = true;
            }
            distSelect.appendChild(option);
        });

        // Show the release info section
        releaseInfoDiv.style.display = 'block';
    }

    function showPackagesTable() {
        if (!packages.length) {
            packageCountDiv.style.display = 'none';
            tableContainerDiv.style.display = 'none';
            return;
        }

        // Get the unique package count
        const filteredPackages = getFilteredPackages();
        const uniquePackageNames = new Set(filteredPackages.map(pkg => pkg.name));
        
        // Update the package count
        packageCountDiv.textContent = `Found ${uniquePackageNames.size} packages (${filteredPackages.length} versions total)`;
        packageCountDiv.style.display = 'block';
        
        // Render the table
        renderTable();
        
        // Show the table container
        tableContainerDiv.style.display = 'block';
    }

    function renderTable() {
        const filteredPackages = getFilteredPackages();
        
        // Group packages by name
        const packageGroups = {};
        filteredPackages.forEach(pkg => {
            if (!packageGroups[pkg.name]) {
                packageGroups[pkg.name] = [];
            }
            packageGroups[pkg.name].push(pkg);
        });
        
        // Convert grouped packages back to an array for pagination
        const groupedPackages = Object.keys(packageGroups).map(name => ({
            name,
            versions: packageGroups[name]
        }));
        
        // Sort the grouped packages
        groupedPackages.sort((a, b) => a.name.localeCompare(b.name));
        
        // Update pagination with the new count
        const totalPages = Math.max(1, Math.ceil(groupedPackages.length / pageSize));
        totalPagesSpan.textContent = totalPages;
        
        // Adjust current page if needed
        if (currentPage > totalPages) {
            currentPage = totalPages;
            pageInput.value = currentPage;
        }
        
        // Update pagination buttons state
        firstPageBtn.disabled = currentPage === 1;
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
        lastPageBtn.disabled = currentPage === totalPages;

        // Calculate start and end indices for current page
        const startIndex = (currentPage - 1) * pageSize;
        const endIndex = Math.min(startIndex + pageSize, groupedPackages.length);
        
        // Clear the table
        packagesTable.innerHTML = '';
        
        // Helper function to build download URL
        function buildDownloadUrl(filename) {
            // Remove any trailing slashes from base URL
            const cleanBaseUrl = repoBaseUrl.replace(/\/+$/, '');
            // Remove any leading slashes from filename and ensure it doesn't start with 'pool/'
            let cleanFilename = filename.replace(/^\/+/, '');
            if (!cleanFilename.startsWith('pool/')) {
                cleanFilename = `pool/${cleanFilename}`;
            }
            // Combine with a single slash
            return `${cleanBaseUrl}/${cleanFilename}`;
        }

        // Add package rows
        for (let i = startIndex; i < endIndex; i++) {
            const packageGroup = groupedPackages[i];
            const row = document.createElement('tr');
            
            // Package name
            const nameCell = document.createElement('td');
            nameCell.textContent = packageGroup.name;
            row.appendChild(nameCell);
            
            // Version cell with dropdown if multiple versions exist
            const versionCell = document.createElement('td');
            
            if (packageGroup.versions.length > 1) {
                // Create dropdown for multiple versions
                const select = document.createElement('select');
                select.className = 'version-dropdown';
                
                packageGroup.versions.forEach(version => {
                    const option = document.createElement('option');
                    option.value = version.version;
                    option.textContent = version.version;
                    option.dataset.filename = version.filename;
                    select.appendChild(option);
                });
                
                // Create download button
                const downloadButton = document.createElement('button');
                downloadButton.className = 'download-button';
                downloadButton.textContent = 'Download';
                
                // Set initial download URL
                const initialPackage = packageGroup.versions[0];
                const initialDownloadUrl = buildDownloadUrl(initialPackage.filename);
                downloadButton.title = initialDownloadUrl;
                downloadButton.onclick = () => {
                    window.open(initialDownloadUrl, '_blank');
                };
                
                // Update download URL when version changes
                select.addEventListener('change', (e) => {
                    const selectedVersion = e.target.value;
                    const selectedPackage = packageGroup.versions.find(v => v.version === selectedVersion);
                    const downloadUrl = buildDownloadUrl(selectedPackage.filename);
                    downloadButton.title = downloadUrl;
                    downloadButton.onclick = () => {
                        window.open(downloadUrl, '_blank');
                    };
                });
                
                versionCell.appendChild(select);
                row.appendChild(versionCell);
                
                // Download button cell
                const downloadCell = document.createElement('td');
                downloadCell.appendChild(downloadButton);
                row.appendChild(downloadCell);
            } else {
                // Single version, no dropdown needed
                const singlePackage = packageGroup.versions[0];
                versionCell.textContent = singlePackage.version;
                row.appendChild(versionCell);
                
                // Download button for single version
                const downloadCell = document.createElement('td');
                const downloadButton = document.createElement('button');
                downloadButton.className = 'download-button';
                downloadButton.textContent = 'Download';
                
                const downloadUrl = buildDownloadUrl(singlePackage.filename);
                downloadButton.title = downloadUrl;
                downloadButton.onclick = () => {
                    window.open(downloadUrl, '_blank');
                };
                
                downloadCell.appendChild(downloadButton);
                row.appendChild(downloadCell);
            }
            
            packagesTable.appendChild(row);
        }
    }

    function getFilteredPackages() {
        if (!searchQuery) {
            return sortPackages([...packages]);
        }
        
        const filtered = packages.filter(pkg => 
            pkg.name.toLowerCase().includes(searchQuery)
        );
        
        return sortPackages(filtered);
    }

    function sortPackages(pkgs) {
        return pkgs.sort((a, b) => {
            const fieldA = a[sortField].toLowerCase();
            const fieldB = b[sortField].toLowerCase();
            
            if (sortDirection === 'asc') {
                return fieldA.localeCompare(fieldB);
            } else {
                return fieldB.localeCompare(fieldA);
            }
        });
    }

    function getTotalPages() {
        // Get grouped package count for pagination
        const filteredPackages = getFilteredPackages();
        const uniquePackageNames = new Set(filteredPackages.map(pkg => pkg.name));
        return Math.max(1, Math.ceil(uniquePackageNames.size / pageSize));
    }

    function showLoading(isLoading) {
        loadButton.disabled = isLoading;
        loadButton.textContent = isLoading ? 'Loading...' : 'Load Repository';
    }

    function showError(message) {
        errorMessageDiv.textContent = message;
        errorMessageDiv.style.display = 'block';
    }

    function clearError() {
        errorMessageDiv.style.display = 'none';
    }

    function hidePackagesInfo() {
        // Hide UI elements
        packagesUrlDiv.style.display = 'none';
        packageCountDiv.style.display = 'none';
        tableContainerDiv.style.display = 'none';
        
        // Clear packages data
        packages = [];
        packagesTable.innerHTML = '';
        packagesUrl = '';
    }

    // Helper functions for parsing
    function parseReleaseFile(content) {
        const info = {};
        const lines = content.split('\n');
        let currentKey = null;
        let currentValue = [];

        for (const line of lines) {
            if (!line.trim()) continue;

            if (line.startsWith(' ')) {
                // Continuation of previous field
                if (currentKey) {
                    currentValue.push(line.trim());
                }
            } else {
                // Save previous field if exists
                if (currentKey) {
                    info[currentKey] = currentValue.length > 1 ? currentValue : currentValue[0];
                    currentValue = [];
                }

                // Parse new field
                const colonIndex = line.indexOf(': ');
                if (colonIndex > 0) {
                    const key = line.substring(0, colonIndex);
                    const value = line.substring(colonIndex + 2).trim();
                    currentKey = key;
                    currentValue = [value];
                }
            }
        }

        // Save last field
        if (currentKey) {
            info[currentKey] = currentValue.length > 1 ? currentValue : currentValue[0];
        }

        // Parse special fields into arrays
        if (info.Architectures) {
            info.Architectures = info.Architectures.split(' ').filter(Boolean);
        }
        if (info.Components) {
            info.Components = info.Components.split(' ').filter(Boolean);
        }

        return info;
    }

    function parsePackages(content) {
        const packages = [];
        const blocks = content.split('\n\n');
        
        for (const block of blocks) {
            if (!block.trim()) continue;
            
            const pkg = {};
            const lines = block.split('\n');
            
            for (const line of lines) {
                const colonIndex = line.indexOf(': ');
                if (colonIndex <= 0) continue;
                
                const key = line.substring(0, colonIndex);
                const value = line.substring(colonIndex + 2).trim();
                
                if (key === 'Package') pkg.name = value;
                else if (key === 'Version') pkg.version = value;
                else if (key === 'Filename') pkg.filename = value;
            }
            
            if (pkg.name && pkg.version && pkg.filename) {
                packages.push(pkg);
            }
        }
        
        return packages;
    }

    function buildPackagesUrl(baseUrl, dist, component, arch) {
        const cleanBaseUrl = baseUrl.replace(/\/$/, '');
        // Check if the base URL already includes the dists directory
        if (cleanBaseUrl.includes('/dists/')) {
            // Extract the base part before /dists/
            const basePart = cleanBaseUrl.split('/dists/')[0];
            // Check if dist is already in the URL
            if (cleanBaseUrl.includes(`/dists/${dist}`)) {
                return `${cleanBaseUrl}/${component}/binary-${arch}/Packages`;
            } else {
                return `${basePart}/dists/${dist}/${component}/binary-${arch}/Packages`;
            }
        }
        return `${cleanBaseUrl}/dists/${dist}/${component}/binary-${arch}/Packages`;
    }

    // Function to reset all state when loading a new repository
    function resetState() {
        // Reset state variables
        releaseInfo = null;
        packagesUrl = '';
        packages = [];
        currentPage = 1;
        pageInput.value = 1;
        searchQuery = '';
        searchQueryInput.value = '';
        availableDists = [];
        
        // Reset UI selectors
        distSelect.innerHTML = '<option value="">Select Distribution</option>';
        archSelect.innerHTML = '<option value="">Select Architecture</option>';
        componentSelect.innerHTML = '<option value="">Select Component</option>';
        
        // Hide all repository-specific UI sections
        releaseInfoDiv.style.display = 'none';
        packagesUrlDiv.style.display = 'none';
        packageCountDiv.style.display = 'none';
        tableContainerDiv.style.display = 'none';
        
        // Clear packages table
        packagesTable.innerHTML = '';
        
        // Clear info grid
        infoGridDiv.innerHTML = '';
    }
}); 
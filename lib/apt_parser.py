"""
Core APT repository parsing functionality
"""

class AptParser:
    """
    Class for parsing APT repository files
    """
    
    @staticmethod
    def parse_release_file(content):
        """
        Parse a Release file content into structured data
        """
        info = {}
        lines = content.split('\n')
        current_key = None
        current_value = []

        for line in lines:
            if not line.strip():
                continue

            if line.startswith(' '):
                # Continuation of previous field
                if current_key:
                    current_value.append(line.strip())
            else:
                # Save previous field if exists
                if current_key:
                    info[current_key] = current_value[0] if len(current_value) == 1 else current_value
                    current_value = []

                # Parse new field
                parts = line.split(': ', 1)
                if len(parts) == 2:
                    key, value = parts
                    current_key = key
                    current_value = [value.strip()]

        # Save last field
        if current_key:
            info[current_key] = current_value[0] if len(current_value) == 1 else current_value

        # Parse special fields into arrays
        if 'Architectures' in info:
            info['Architectures'] = info['Architectures'].split(' ')
            info['Architectures'] = [arch for arch in info['Architectures'] if arch]
            
        if 'Components' in info:
            info['Components'] = info['Components'].split(' ')
            info['Components'] = [comp for comp in info['Components'] if comp]

        return info

    @staticmethod
    def parse_packages(content):
        """
        Parse a Packages file content into structured data
        """
        packages = []
        blocks = content.split('\n\n')
        
        for block in blocks:
            if not block.strip():
                continue
                
            pkg = {}
            lines = block.split('\n')
            
            for line in lines:
                parts = line.split(': ', 1)
                if len(parts) != 2:
                    continue
                    
                key, value = parts
                value = value.strip()
                
                if key == 'Package':
                    pkg['name'] = value
                elif key == 'Version':
                    pkg['version'] = value
                elif key == 'Filename':
                    pkg['filename'] = value
            
            if all(k in pkg for k in ['name', 'version', 'filename']):
                packages.append(pkg)
        
        return packages

    @staticmethod
    def build_packages_url(base_url, codename, component, arch):
        """
        Build a Packages URL from components
        """
        clean_base_url = base_url.rstrip('/')
        # Check if the base URL already includes the dists directory
        if '/dists/' in clean_base_url:
            # Extract the base part before /dists/
            base_part = clean_base_url.split('/dists/')[0]
            # Check if codename is already in the URL
            if f"/dists/{codename}" in clean_base_url:
                return f"{clean_base_url}/{component}/binary-{arch}/Packages"
            else:
                return f"{base_part}/dists/{codename}/{component}/binary-{arch}/Packages"
        return f"{clean_base_url}/dists/{codename}/{component}/binary-{arch}/Packages" 
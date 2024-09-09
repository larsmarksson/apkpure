from typing import Dict


class SearchResult:
    app_title: str = ''
    developer: str = ''
    icon: str = ''
    package_name: str = ''
    package_size: int = 0
    package_version: str = ''
    package_version_code: int = 0
    download_link: str = ''
    package_url: str = ''

    def __init__(self, details: Dict):
        for key, value in details.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                # Debugging: Warn about unmatched keys
                print(f"Warning: {key} is not a recognized attribute")

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.app_title} v{self.package_version}>"

    def __str__(self):
        return self.__dict__.__str__()

    def update(self, details: Dict):
        for key, value in details.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def _version_tuple(self) -> tuple:
        """Helper method to convert the version string into a tuple of integers for comparison."""
        return tuple(map(int, self.package_version.split('.')))

    def __lt__(self, other):
        if isinstance(other, SearchResult):
            return self._version_tuple() < other._version_tuple()
        return NotImplemented

    def __eq__(self, other):
        if isinstance(other, SearchResult):
            return self._version_tuple() == other._version_tuple()
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, SearchResult):
            return self._version_tuple() > other._version_tuple()
        return NotImplemented

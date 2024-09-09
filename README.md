
# Apk Pure API

This is a fork of [anishomsy's ApkPure API](https://github.com/anishomsy/apkpure). In this version, several changes were made to return instances of the `SearchResult` class rather than JSON objects, allowing for more programmatic operations and better integration into workflows requiring detailed APK data.

## Key Changes

### Introduction of the `SearchResult` Class

The `SearchResult` class is now used to represent the results of app searches and metadata retrieval. This allows for direct manipulation of the returned data, enabling more complex operations such as version comparison, detailed information extraction, and cleaner, more maintainable code.

The `SearchResult` class has the following attributes:
- `app_title`: The title of the app.
- `developer`: The name of the app's developer.
- `icon`: URL of the app's icon.
- `package_name`: The app's package name.
- `package_size`: The size of the app package in bytes.
- `package_version`: The current version of the app.
- `package_version_code`: The version code of the app.
- `download_link`: URL to download the app.
- `package_url`: URL of the app's page on APK Pure.

The class includes comparison methods (`__lt__`, `__eq__`, `__gt__`) that allow comparing app versions by their `package_version`. Additionally, the `__repr__` and `__str__` methods have been overridden to provide meaningful string representations of the `SearchResult` object.

### Modifications to `apkpure.py`

- **Returning `SearchResult` Instances**: 
  All methods that previously returned JSON data (such as `search_all`, `search_exact`, and `get_versions`) now return instances of the `SearchResult` class. This change improves flexibility when working with APK data in the code, allowing developers to use object-oriented features like attribute access and method overrides.

  Example usage:
  ```python
  from apkpure import ApkPure
  
  api = ApkPure()
  search_result = api.search_exact("WhatsApp")
  
  if search_result:
      print(search_result.app_title)  # Access app title directly
  ```

- **Improved Search and Data Retrieval**:
  The data extraction from APK Pure's HTML has been refactored to build `SearchResult` instances rather than constructing raw dictionaries or JSON strings. This allows developers to work with strongly typed objects in their code.

- **New Methods for Comparison**:
  The `SearchResult` class includes comparison methods (`__lt__`, `__eq__`, `__gt__`) that make it easy to compare app versions. This feature can be used to automatically determine whether a newer version of an app is available, simplifying update logic.

  Version strings like `'3.2.12'` and `'3.11.12'` are now correctly compared using a tuple-based version comparison approach.

### Usage Example

Here’s how you can now search for an app and retrieve detailed information using the `SearchResult` class:

```python
from apkpure import ApkPure

# Initialize ApkPure
api = ApkPure()

# Search for an app and get the exact result
search_result = api.search_exact("WhatsApp")
if search_result:
    print(f"Found app: {search_result.app_title}")
    print(f"Current version: {search_result.package_version}")
    print(f"Download link: {search_result.download_link}")

# Compare versions (for example, with a known version)
if search_result.package_version > "2.21.1.15":
    print("A newer version is available.")
```

This allows for cleaner, object-oriented management of APK data and significantly simplifies version management when working with APK Pure's data.

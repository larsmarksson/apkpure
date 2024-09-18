import json
import os
import time
from typing import Union, Dict, List

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import re
import sys
import cloudscraper

from apkpure.AppInfo import AppInfo
from apkpure.SearchResult import SearchResult


class ApkPure:
    def __init__(self, headers: dict | None = None) -> None:
        if headers is None:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:47.0) Gecko/20100101 Firefox/47.0"
            }
        self.headers = headers
        self.query_url = "https://apkpure.com/search?q="

    def check_name(self, name):
        name = name.strip()
        if not name:
            sys.exit(
                "No search query provided!",
            )

    def __helper(self, url) -> BeautifulSoup:
        while True:
            try:
                response = self.get_response(url=url)
                soup = BeautifulSoup(response.text, "html.parser")

                # Check for Cloudflare protection or an error page
                if soup.find_all("div", {"class": "core-msg"}):
                    print('Cloudflare encountered. Fetching unsuccessful. Waiting 5 seconds before retry.')
                    time.sleep(5)
                    continue  # Retry fetching the URL after a delay

                # If no Cloudflare issues, return the parsed HTML
                return soup

            except Exception as e:
                raise Exception(f"Failed to fetch or parse content from {url}: {str(e)}")

    def get_response(self, url: str, **kwargs) -> requests.Response:
        try:
            response = requests.get(url, headers=self.headers, **kwargs)

            if response.status_code == 403:  # If blocked by Cloudflare
                scraper = cloudscraper.create_scraper()  # Create a scraper to bypass protection
                response = scraper.get(url=url, **kwargs)

            # Return the response if the status code is 200, else raise an exception
            if response.status_code == 200:
                return response
            raise Exception(f"Failed to fetch URL: {url}, Status code: {response.status_code}")

        except requests.exceptions.RequestException as e:
            # Catch any network-related errors (like connection issues, timeouts, etc.)
            raise Exception(f"Error during requests to {url}: {str(e)}")

    def extract_info_from_search(self, html_element) -> Dict:
        def get_basic_info() -> dict:
            title = html_element.find("p", class_="p1")
            developer = html_element.find("p", class_="p2")
            return {
                "app_title": title.text.strip() if title else "Unknown",
                "developer": developer.text.strip() if developer else "Unknown",
            }

        def get_package_url() -> dict:
            # Try finding the correct URL element, raising an exception if not found
            package_url = html_element.find("a", class_="first-info") or html_element.find("a", class_="dd")
            if package_url:
                return {"package_url": package_url.get("href", "Unknown")}
            else:
                raise Exception("Package URL not found in search result")

        def get_icon() -> dict:
            # Check if the image element exists, otherwise return "Unknown"
            icon = html_element.find("img")
            return {"icon": icon.get("src", "Unknown") if icon else "Unknown"}

        def get_package_data() -> dict:
            # Try finding the appropriate package data, ensuring it exists
            package_data = html_element if html_element.find('a', class_="first-info") else html_element.find("a",
                                                                                                              class_="is-download")
            if not package_data:
                raise Exception("Package data not found in search result")
            return {
                "package_name": package_data.get("data-dt-app", "Unknown"),
                "package_size": package_data.get("data-dt-filesize", "Unknown"),
                "package_version": package_data.get("data-dt-version", "Unknown"),
                "package_version_code": package_data.get("data-dt-versioncode", "Unknown"),
            }

        def get_download_link() -> dict:
            # Try finding the download link, raising an exception if not found
            download_link = html_element.find("a", class_="is-download") or html_element.find("a", class_="da")
            if download_link:
                return {"download_link": download_link.get("href", "Unknown")}
            else:
                raise Exception("Download link not found in search result")

        # Extract information by calling the sub-functions
        try:
            basic_info = get_basic_info()
            package_url = get_package_url()
            icon = get_icon()
            package_data = get_package_data()
            download_link = get_download_link()

        except Exception as e:
            print(f"Error extracting app info: {str(e)}")
            return {}  # Return an empty dictionary or handle this gracefully

        # Combine all the extracted info into a single dictionary
        return {**basic_info, **package_url, **icon, **package_data, **download_link}

    def search_top(self, name: str) -> SearchResult:
        # Check that a valid search name is provided
        self.check_name(name)

        try:
            # Create the query URL using the search term
            query_url = self.query_url + name

            # Fetch and parse the HTML response
            soup_obj = self.__helper(query_url)

            # Find the first app result
            first_div = soup_obj.find("div", class_="first")
            if first_div is None:
                raise Exception(f"App not found for search query: {name}")

            # Extract the first result's package URL, or raise an error if it's not available
            package_url = first_div.find("a", class_="first-info") or first_div.find("a", class_="dd")
            if package_url is None:
                raise Exception(f"Package URL not found for the first app in search results: {name}")

            # Extract the app info
            result_data = self.extract_info_from_search(first_div)

            # Create a SearchResult object from the extracted data
            search_result = SearchResult(result_data)

            # Return the SearchResult object
            return search_result

        except Exception as e:
            # Raise a clear error message if something goes wrong
            raise Exception(f"Failed to retrieve top search result for '{name}': {str(e)}")

    def search_all(self, name: str) -> list[SearchResult]:
        self.check_name(name)

        url = self.query_url + name
        soup = self.__helper(url)

        first_app = soup.find("div", class_="first")
        list_of_apps = soup.find("ul", id="search-res")  # UL
        apps_in_list_of_apps = list_of_apps.find_all("li")  # LI's

        all_results = [self.extract_info_from_search(first_app)]

        for app in apps_in_list_of_apps:
            all_results.append(self.extract_info_from_search(app))

        results = [SearchResult(res) for res in all_results]
        return results

    def search_exact(self, app_title: str) -> SearchResult:
        results = self.search_all(app_title)
        for app in results:
            if app.app_title == app_title:
                return app
        raise Exception(f"No exact match found for app title: {app_title}")

    def get_latest_version(self, app_title: str = None, package_name: str = None) -> SearchResult:
        return self.get_versions(app_title=app_title, package_name=package_name)[0]

    def get_versions(self, app_title: str = None, package_name: str = None) -> list[SearchResult]:
        if not app_title and not package_name:
            raise Exception("Either app_title or package_name must be provided to retrieve versions.")

        try:
            # Get all search results for the provided app title
            results = self.search_all(app_title)

            # Find the matching app by title or package name
            target_result = None
            for result in results:
                if result.package_name == package_name or result.app_title == app_title:
                    target_result = result
                    break

            if target_result is None:
                raise Exception(f"No matching app found for title: {app_title} or package name: {package_name}")

            # Construct the URL to fetch versions
            url = f"{target_result.package_url}/versions"
            soup = self.__helper(url)

            # Parse the available versions
            available_versions = []
            ul = soup.find("ul", class_="ver-wrap")
            if ul is None:
                raise Exception("No versions found for the app")

            lists = ul.find_all("li")
            if not lists:
                raise Exception("No version list available")

            # Iterate over each version entry in the list
            for li in lists:
                dl_btn = li.find("a", class_="ver_download_link")
                if not dl_btn:
                    continue
                dl_btn = dl_btn.attrs
                package_version = dl_btn.get("data-dt-version", "Unknown")
                download_link = dl_btn.get("href", "Unknown")
                package_version_code = dl_btn.get("data-dt-versioncode", "Unknown")

                # Create a new SearchResult object for each version, based on the original app info
                version_info = {
                    "package_version": package_version,
                    "download_link": download_link,
                    "package_version_code": package_version_code,
                }
                new_version = SearchResult(target_result.__dict__)  # Use the base app info from target_result
                new_version.update(version_info)  # Add version-specific data
                available_versions.append(new_version)

            # Return the list of SearchResult objects for each version
            return available_versions

        except Exception as e:
            # Raise a clear error message if something goes wrong
            raise Exception(f"Failed to retrieve versions for '{app_title}' or '{package_name}': {str(e)}")

    def get_info(self, app_title: str) -> AppInfo:
        try:
            # Search for the exact app to get its basic info
            result = self.search_exact(app_title)
            if result is None:
                raise Exception(f"No exact match found for app title: {app_title}")

            # Use the package URL to fetch more details about the app
            url = result.package_url
            soup = self.__helper(url)

            # Find the relevant div containing the app details
            divs = soup.find("div", class_="detail_banner")
            if divs is None:
                raise Exception(f"Could not find app details for '{app_title}'")

            # Extract title, rating, date, developer, etc.
            title = divs.find("div", class_="title_link").get_text(strip=True)
            rating = divs.find("span", class_="rating")
            rating = rating.get_text(strip=True) if rating else "No rating available"

            date = divs.find("p", class_="date").get_text(strip=True)
            sdk_info = divs.find("p", class_="details_sdk")
            latest_version = sdk_info.contents[1].get_text(strip=True)
            developer = sdk_info.contents[3].get_text(strip=True)

            # Extract download button info for package name and version code
            dl_btn = divs.find("a", class_="download_apk_news").attrs
            package_name = dl_btn["data-dt-package_name"]
            package_version_code = dl_btn["data-dt-version_code"]
            download_link = dl_btn["href"]

            # Find the description
            description = soup.find("div", class_="translate-content")
            description = description.get_text(strip=True) if description else "No description available"

            # Fetch older versions of the app using the get_versions function
            versions = self.get_versions(app_title)

            # Create and return an AppInfo object
            app_info = AppInfo(
                app_title=title,
                rating=rating,
                date=date,
                latest_version=latest_version,
                description=description,
                developer=developer,
                package_name=package_name,
                package_version_code=package_version_code,
                download_link=download_link,
                older_versions=versions
            )

            return app_info

        except Exception as e:
            # Raise a clear error message if something goes wrong
            raise Exception(f"Failed to retrieve information for '{app_title}': {str(e)}")

    def download(self, search_result: SearchResult = None, app_title: str = None, version: str = None) -> str:
        # Ensure that either a valid SearchResult or app_title is provided
        if not any([search_result, app_title]):
            raise Exception("Either SearchResult or app_title must be provided to perform download.")

        try:
            if not search_result and version is None:
                search_result = self.get_latest_version(app_title)
            if not search_result and version is not None:
                available_versions = self.get_versions(app_title)
                #  will raise IndexError if no versions found
                search_result = [ver for ver in available_versions if ver.package_version == version][0]

            # Construct the download URL
            base_url = "https://d.apkpure.com/b/XAPK/"
            download_url = f"{base_url}{search_result.package_name}?versionCode={search_result.package_version_code}"

            print(f"Downloading version {search_result.package_version} from {download_url}")

            # Call the downloader method to handle the file download
            return self.downloader(download_url, f'{search_result.package_name}_{search_result.package_version}.xapk')
        except IndexError:
            raise Exception(f"No versions found for '{app_title}'")
        except Exception as e:
            raise Exception(f"Failed to download APK for '{app_title or search_result.app_title}': {str(e)}")

    def downloader(self, url: str, filename) -> str:
        try:
            response = self.get_response(url=url, stream=True, allow_redirects=True)

            # Create the download path
            fname = os.path.join(os.getcwd(), f"apks/{filename}")
            os.makedirs(os.path.dirname(fname), exist_ok=True)

            # If the file already exists, skip download
            if os.path.exists(fname) and int(response.headers.get("content-length", 0)) == os.path.getsize(fname):
                print("File already exists!")
                return os.path.realpath(fname)

            # Download the file in chunks and save it to disk
            with tqdm.wrapattr(
                    open(fname, "wb"), "write", miniters=1, total=int(response.headers.get("content-length", 0))
            ) as file:
                for chunk in response.iter_content(chunk_size=4 * 1024):
                    if chunk:
                        file.write(chunk)

            return os.path.realpath(fname)

        except Exception as e:
            raise Exception(f"Failed to download file from {url}: {str(e)}")

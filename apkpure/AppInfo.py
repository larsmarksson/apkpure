class AppInfo:
    def __init__(self, app_title: str, rating: str, date: str, latest_version: str,
                 description: str, developer: str, package_name: str,
                 package_version_code: str, download_link: str, older_versions: list):
        self.app_title = app_title
        self.rating = rating
        self.date = date
        self.latest_version = latest_version
        self.description = description
        self.developer = developer
        self.package_name = package_name
        self.package_version_code = package_version_code
        self.download_link = download_link
        self.older_versions = older_versions

    def __repr__(self):
        return f"AppInfo({self.app_title}, {self.developer}, {self.latest_version})"

    def to_dict(self):
        return {
            "app_title": self.app_title,
            "rating": self.rating,
            "date": self.date,
            "latest_version": self.latest_version,
            "description": self.description,
            "developer": self.developer,
            "package_name": self.package_name,
            "package_version_code": self.package_version_code,
            "download_link": self.download_link,
            "older_versions": [version.to_dict() for version in self.older_versions]
        }

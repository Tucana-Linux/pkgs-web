from dataclasses import asdict
import datetime
import os
from pathlib import Path
import shutil
from jinja2 import Environment, FileSystemLoader, Template

from pkgs_web.classes.WebPackage import WebPackage
from pkgs_web.classes.WebRepository import WebRepository

class WebGenerator:
    """
    Generates all the HTML from templates
    """
    def __init__(self, output_dir : str, repository: WebRepository) -> None:
        self._repository = repository
        Path(f"{output_dir}/www/packages").mkdir(parents=True, exist_ok=True)
        self._www_dir = f"{output_dir}/www"
        self._packages_dir=f"{self._www_dir}/packages"
        self._environment : Environment = Environment(loader=FileSystemLoader("template-html/"))
    
    def prepare_www(self) -> None:
        """
        Prepares the www directory
        """
        shutil.copytree("template-html/css", f"{self._www_dir}/css", dirs_exist_ok=True)
        
    def format_size(kb : int) -> str:
        """
        Used for install_size and download_size
        to convert to useable units
        """
        size = kb * 1024  # Convert KB to bytes
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
        
        
    def generate_package_pages(self) -> None:
        """
        Generates the package html from the templates 
        Precondition: repository is fully initalized 
        with repo.packages available
        """
        package_template : Template = self._environment.get_template("package-template.html")
        for package_name, package in self._repository.packages.items():
            package_dict = asdict(package)
            package_dict["last_update"] = datetime.datetime.fromtimestamp(package["last_update"], tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            package_dict["last_commit"] = datetime.datetime.fromtimestamp(package["last_commit"], tz=datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
            package_dict["download_size"] = self.format_size(package_dict["download_size"])
            package_dict["install_size"] = self.format_size(package_dict["install_size"])
            
            content : str = package_template.render(
            package_dict,
            package_name=package_name)
            with open(f"{self._packages_dir}/{package_name}.html", "w") as file:
                file.write(content)
                print(f"Generated template for {package_name}")



    def generate_home_page(self, numLatestPackages: int):
        """
        Generate the home page from HTML
        """
        # not sorted :(
        latest_packages : list[WebPackage] = sorted(self._repository.packages.values(), key=lambda pkg: pkg.last_update, reverse=True)[:numLatestPackages] 
        template : Template = self._environment.get_template("front-page.html")
        content : str = template.render(latest_packages=latest_packages)
        with open(f"{self._www_dir}/homepage.html", "w") as file:
            file.write(content)

    #def copy_search_components(self):


    



        
    
    
    
    
    
    

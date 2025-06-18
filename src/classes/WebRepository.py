"""
Takes a regular neptune repository and adds the parameters 
pkgs-web needs from a build-scripts directory and other
outside metadata
"""
import logging
import sys
from typing import Any
from neptune.classes.Package import Package
import requests
import yaml

from classes.WebPackage import WebPackage


class WebRepository:
    def __init__(self, url: str, name:str):
        self.url = url
        self.name = name
        self._packages : dict[str, Package] = {}
        self._web_packages: dict[str, WebPackage]
   
    def retrieve_packages(self) -> None:
        """
        Retrieves packages.yaml from the given repository 
        and processes it
        """
        packages_url = f"{self.url}/available-packages/packages.yaml"
    
        print(f"Attempting to retrieve packages from: {packages_url}")
    
        try:
            response = requests.get(packages_url)
            response.raise_for_status()
            yaml_data : dict[str, dict[str, Any]] = {}
            try: 
                yaml_data = yaml.load(response.text, yaml.CSafeLoader)
            except Exception as e :
                logging.error(f"This does not seem to be a valid yaml file {e}")

            for package_name, package in yaml_data.items():
                # The package name is already available from the dictionary key,
                # so we use it directly instead of getting it from 'item.get('name')'.
                # The 'name' field in the Package object will be set from the key.
                try:
                    new_package = Package(
                        name=package_name, 
                        version=package["version"],
                        download_size=int(package["download_size"]),
                        install_size=int(package["install_size"]),
                        repo=package["repo"],
                        last_update=int(package["last_update"]),
                        depends=package["depends"],
                        make_depends=package["make_depends"],
                        wanted=False
                    )
                    self._packages[new_package.name] = new_package
                except KeyError as e:
                    logging.error(f"Missing required key in package data for '{package_name}': {e} in {package}")
                except TypeError as e:
                    logging.error(f"Type mismatch when creating Package object for '{package_name}': {e} in {package}")
            if not self._packages:
                logging.error("Could not load/retrieve packages.yaml")
                sys.exit(1)
            print(f"Successfully loaded {len(self._packages)} packages.")
            return
        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP error occurred: {e}")
            sys.exit(1)
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error occurred: {e}")
            sys.exit(1)
        except requests.exceptions.Timeout as e:
            logging.error(f"The request timed out: {e}")
            sys.exit(1)
        except requests.exceptions.RequestException as e:
            logging.error(f"An unexpected request error occurred: {e}")
            sys.exit(1)
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            sys.exit(1)
    
    def packages_to_web_packages(self) -> None:
        """
        Precondition self.packages is not falsly
        Takes the dict[str, Packages] and turns it
        into dict[str, WebPackages] adding parameters
        like reverse dependencies, build commit date
        Source URL and Build Log
        """
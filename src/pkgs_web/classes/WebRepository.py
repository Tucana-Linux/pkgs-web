"""
Takes a regular neptune repository and adds the parameters 
pkgs-web needs from a build-scripts directory and other
outside metadata
"""
import logging
import os
import subprocess
import sys
from typing import Any, Tuple
from neptune.classes.Package import Package
import requests
import yaml

from pkgs_web.classes.WebPackage import WebPackage

"""
This is used to read any neptune repository
Precondition: build-scripts in $GIT_LOCATION/build-scripts
(Build Scripts are used to add parameters)
After init run 
repo.retrieve_packages(), 
repo.packages_to_web_packages() 
"""
class WebRepository:

    def __init__(self, url: str, name:str):
        self.url = url
        self.name = name
        self._neptune_packages : dict[str, Package] = {}
        self._web_packages: dict[str, WebPackage] = {}
        self._root_directory = os.curdir
        self._build_script_path = os.path.join(os.curdir, "build-scripts")
   
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
                        repo=self.name,
                        last_update=int(package["last_update"]),
                        depends=package["depends"],
                        make_depends=package["make_depends"],
                        wanted=False
                    )
                    self._neptune_packages[new_package.name] = new_package
                except KeyError as e:
                    logging.error(f"Missing required key in package data for '{package_name}': {e} in {package}")
                except TypeError as e:
                    logging.error(f"Type mismatch when creating Package object for '{package_name}': {e} in {package}")
            if not self._neptune_packages:
                logging.error("Could not load/retrieve packages.yaml")
                raise RuntimeError("Could not load/retrieve packages.yaml")
            logging.info(f"Successfully loaded {len(self._neptune_packages)} packages.")
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
        Takes the dict[str, Package] (self._neptune_packages) and turns it
        into dict[str, WebPackage] adding parameters
        like reverse dependencies, build commit date
        Source URL and Build Log
        """

        def find_build_script(package_name : str) -> str:
            """
            Take package name and output the relative path to the build script 
            """
            build_script : str = ""
            build_script = subprocess.run(f"find . -type f -name {package_name}", shell=True, capture_output=True, text=True).stdout.strip()
            if not build_script:
                build_script = subprocess.run(f"grep -rE '.*PACKAGE.*={package_name}' | sed 's/:.*//g' | head -1", capture_output=True, text=True, shell=True).stdout.strip()
            if not build_script:
                logging.error("Could not find build-script")
                raise FileNotFoundError
            return build_script

        def extract_build_script_info(build_script_location: str) -> Tuple[int, str]:
            """
            Take the build script location and output the relevant info
            Index Table
            1 - Last Commit
            2 - Source URL
            """
            #WARNING: This function explicitly passes things from the build script into eval (bash), check your build scripts setters before pushing them!

            # TODO this is incredibly stupid and insecure, add metadata to neptune for the next update
            source_url_command = f"""bash -c 'eval "$(head -n "$(grep -n '^URL=' {build_script_location}| head -1 | cut -d: -f1)" {build_script_location})" && echo "$URL"'"""
            source_url : str = subprocess.run(source_url_command, shell=True, capture_output=True, text=True).stdout.strip()


            if not os.path.isdir(".git"):
                logging.error("Not a git repository!")
                raise FileNotFoundError

            commit_output = subprocess.run(f"git log -1 --format=%ct -- {build_script_location}", shell=True, capture_output=True, text=True, cwd=self._build_script_path).stdout.strip()

            if not commit_output:
                raise RuntimeError(f"Could not get git commit history for {build_script_location}")

            last_commit : int = int(commit_output)
            
            return (last_commit, source_url)

        def find_reverse_depends(search_package_name: str) -> list[str]:
            reverse_depends : set[str] = set()
            for package_name, package in self._neptune_packages.items():
                if search_package_name in (package.depends or []):
                    reverse_depends.add(package_name)
                
            return list(reverse_depends)


        for package_name, package in self._neptune_packages.items():
            # To find build-script
            # Method 1 -- Basic Find -- find . -type f -name package_name
            # Method 2 -- Find Split Package -- grep -rE '.*PACKAGE.*=package_name' | sed 's/:.*//g'
            build_script_location = find_build_script(package_name)
            package_build_info : Tuple[int, str] = extract_build_script_info(build_script_location)
            last_commit = package_build_info[0]
            source_url = package_build_info[1]
            reverse_depends = find_reverse_depends(package_name)

            self._web_packages[package_name] = WebPackage.create_from_package(package, last_commit=last_commit, source_url=source_url, build_script_location=build_script_location, reverse_depends=reverse_depends)



    @property
    def packages(self) -> dict[str, WebPackage]:
        return self._web_packages
        

    

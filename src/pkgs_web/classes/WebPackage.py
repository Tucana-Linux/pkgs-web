from dataclasses import asdict, dataclass, field
from neptune.classes.Package import Package

@dataclass
class WebPackage(Package):

    """
    The neptune package class with more attributes
    """
    # need to provide default values to make pylance happy
    last_commit: int = 0
    source_url: str = "example.com"
    reverse_depends: list[str] = field(default_factory=list[str])
    # relative path to build script used in the URL stage
    build_script_location: str = ""
    

    @classmethod
    def create_from_package(cls, neptune_package: Package, last_commit: int, source_url: str, reverse_depends: list[str], build_script_location: str):
        # cheaty workaround to make sure that metadata modified in Neptune will be inherited here
        return cls(last_commit=last_commit, source_url=source_url, reverse_depends=reverse_depends, build_script_location=build_script_location, **asdict(neptune_package))


        


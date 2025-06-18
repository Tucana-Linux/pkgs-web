from neptune.classes.Package import Package

class WebPackage(Package):
    last_rebuild: int
    source_url: str
    reverse_depends: list[str]
    


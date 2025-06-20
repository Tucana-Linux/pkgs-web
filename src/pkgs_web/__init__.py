import argparse

from pkgs_web.classes.WebGenerator import WebGenerator
from pkgs_web.classes.WebRepository import WebRepository

output_directory : str = ""
url : str = ""
name : str = ""
parser = argparse.ArgumentParser(description="Generate a web viewer for Tucana Packages")

parser.add_argument("--url", type=str, help="Specify the URL",required=True)
parser.add_argument("--name", type=str, help="Specify the name of the repository", required=True)
parser.add_argument("--output", type=str, help="Specify the output directory of the html files", required=True)
args = parser.parse_args()

repo : WebRepository = WebRepository(url=args.url, name=args.name)
repo.retrieve_packages()
repo.packages_to_web_packages()

generator: WebGenerator = WebGenerator(repository=repo, output_dir=args.output)

generator.prepare_www()
generator.generate_package_pages()
generator.generate_home_page(100)










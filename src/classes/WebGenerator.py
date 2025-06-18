from jinja2 import Environment, FileSystemLoader, Template

class WebGenerator:

        
    def generate_package_pages(self):
        """
        Generates the package html from the templates 
        Precondition: self.packages is set
        """
        environment : Environment = Environment(loader=FileSystemLoader("template-html/"))
        package_template : Template = environment.get_template("package-template.html")

    def generate_home_page(self):

    def copy_search_components(self):

    def generate_www_dir(self):

    



        
    
    
    
    
    
    
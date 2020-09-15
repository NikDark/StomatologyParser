from parser_searcher_part_1 import search_stomatology as collect_links
from parser_searcher_part_2 import main as link_processing

def make_all():
    # Collect links to sites in the issuance of search engines
    collect_links()
    # Collect data from each site
    link_processing()

if __name__ == "__main__":
    make_all()
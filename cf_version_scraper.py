import json

import bs4.element
from bs4 import BeautifulSoup

import utils


def scrape(filename):
    versions_html = open(filename).read()
    utils.finish_log_action()

    utils.log_action("Parsing HTML")
    soup = BeautifulSoup(versions_html, "html.parser")
    utils.finish_log_action()

    versions_dict = {}

    utils.log_action("Extracting versions")
    for element in soup.find_all("input", {"class": "form-game-version-container", "type": "checkbox"}):
        versions_dict[element.parent.text.strip()] = int(element["value"])

    for element in soup.find("select", {"class": "select form-game-version-container"}):
        if not isinstance(element, bs4.element.Tag) or not element["value"]:
            continue
        versions_dict[element.text.strip()] = int(element["value"])

    utils.finish_log_action()

    utils.log_action("Saving results")
    output_file = open("cf_version_mappings.json", "w")
    output_file.write(json.dumps(versions_dict, indent=4))
    output_file.close()
    utils.finish_log_action()

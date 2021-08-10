#! python

import argparse
import json
import zipfile

import colorama
import toml
from termcolor import colored

import cf_version_scraper
import host_adapters
import utils
from utils import fail, log_action, finish_log_action

# Make sure we get a colored terminal on windows
colorama.init()

# Parse arguments
parser = argparse.ArgumentParser(description="Upload artifacts to various mod hosting sites",
                                 usage="%(prog)s config_file artifact [--modrinth] [--curseforge]")

parser.add_argument("config_file", help="The upload config to use", nargs="?")
parser.add_argument("artifact", help="The artifact to upload", nargs="?")

parser.add_argument("-m", "--modrinth", help="Don't ask, always upload to Modrinth", action="store_true")
parser.add_argument("-c", "--curseforge", help="Don't ask, always upload to CurseForge", action="store_true")
parser.add_argument("-l", "--loader", help="Overrides the modloader defined in config, required if none is defined",
                    type=str, choices=["forge", "fabric"])
parser.add_argument("-f", "--find-artifact",
                    help="Interpret artifact filename as version ID and search using the given pattern in the given directory",
                    action="store_true")
parser.add_argument("--scrape-cf-mappings",
                    help="Scrape CurseForge version mappings from the given HTML and exit",
                    type=str, metavar="<mod edit page HTML>")
parser.add_argument("--dump-cf-mappings",
                    help="Dumps the currently indexed CurseForge version IDs",
                    action="store_true")
parser.add_argument("--debug", help="Prints the requests being sent to the host sites", action="store_true")

args = parser.parse_args()
print("\n\u001b[38;5;100mScatter™ Mod Publishing Utility - v0.3-beta\u001b[0m\n")

# Verify input
if not args.scrape_cf_mappings and not args.config_file and not args.artifact and not args.dump_cf_mappings:
    parser.print_help()
    exit()

if args.scrape_cf_mappings:
    html_name = args.scrape_cf_mappings

    log_action("Reading versions HTML")

    utils.verify_is_file(html_name, "Versions HTML not found")
    cf_version_scraper.scrape(html_name)

    exit()

utils.verify_is_file("tokens.json", "No token config provided")
utils.verify_is_file("cf_version_mappings.json", "Missing CF version mappings")

if args.dump_cf_mappings:

    log_action("Loading CurseForge mappings")
    mappings = json.loads(open("cf_version_mappings.json").read())
    finish_log_action()

    print(colored("\n-- Begin CF Mappings Dump --\n", "green"))
    lineIndex = 0
    line = ""
    for version in mappings:
        newContent = version + ": " + str(mappings[version])
        line = line + newContent + (" " * (30 - len(newContent)))
        if lineIndex < 3:
            lineIndex = lineIndex + 1
        else:
            print(line)
            lineIndex = 0
            line = ""

    if line:
        print(line)

    print(colored("\n-- End CF Mappings Dump --", "green"))
    exit()


utils.verify_is_file(args.config_file, "Invalid config filename")

# Read upload config
config_filename = args.config_file
log_action("Reading and verifying upload config")

config = utils.verify_schema_and_open(config_filename, utils.CONFIG_SCHEMA)

if args.loader:
    config["modloader"] = args.loader
elif "modloader" not in config:
    fail("Loader has to be given as argument when not defined in config")

finish_log_action()

log_action("Finding artifact file")

# Parse artifact name
artifact_filename = args.artifact

if args.find_artifact:
    utils.verify_json_schema(config_filename, config, utils.ARTIFACT_SEARCH_SCHEMA)
    artifact_filename = config["artifact_directory"] + config["artifact_filename_pattern"].replace("{}", args.artifact)

# Verify artifact exists
utils.verify_is_file(artifact_filename, "Unable to find artifact file")

finish_log_action()

# Read API tokens
log_action("Reading API tokens")

tokens = utils.verify_schema_and_open("tokens.json", utils.TOKEN_SCHEMA)
cf_token = tokens["curseforge"]
modrinth_token = tokens["modrinth"] if "modrinth" in tokens else None

finish_log_action()

# Read version from archive
log_action("Reading version from artifact")

version = None
artifact_jar = zipfile.ZipFile(artifact_filename, "r")

if config["modloader"] == "fabric":
    if not utils.verify_file_in_zip(artifact_jar, "fabric.mod.json"):
        fail("Provided artifact is not a fabric mod")

    mod_json = json.loads(artifact_jar.open("fabric.mod.json").read())
    version = mod_json["version"]
elif config["modloader"] == "forge":
    if not utils.verify_file_in_zip(artifact_jar, "META-INF/mods.toml"):
        fail("Provided artifact is not a forge mod")

    mod_toml = toml.loads(artifact_jar.open("META-INF/mods.toml").read().decode("ascii"))
    version = mod_toml["mods"][0]["version"]

finish_log_action()

# Read user input for this specific version
print()
input_data = {"changelog": utils.colored_input("Changelog: "),
              "version": version if version else utils.colored_input("Version: ")}

release_type = utils.parse_release_type("Release Type: ")
while release_type not in utils.VALID_RELEASE_TYPES:
    release_type = utils.parse_release_type("Invalid type. Try again: ", "red")

input_data["releaseType"] = release_type

print(colored("\nA build with the following metadata will be published:\n", "cyan"))

utils.pretty_print_property("Changelog", input_data["changelog"])
utils.pretty_print_property("Version", version + colored(" (" + release_type + ")", "blue"))
utils.pretty_print_property("Name", utils.format_version_string(config, version) + "\n")

if (args.modrinth or args.curseforge) and not utils.confirm("Proceed?"):
    exit(0)

if args.modrinth or args.curseforge:
    print()

# Give the option to upload to both platforms
if args.curseforge or utils.confirm("Upload to CurseForge?"):
    host_adapters.upload_curseforge(artifact_filename, cf_token, config, input_data, args.debug)

if modrinth_token and "modrinth_id" in config and (args.modrinth or utils.confirm("Upload to Modrinth?")):
    host_adapters.upload_modrinth(artifact_filename, modrinth_token, config, input_data, args.debug)

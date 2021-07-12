import sys
import zipfile
import json

import host_adapters
import utils

# Verify input
utils.verify_is_file("tokens.json", "No token config provided")

utils.verify_arg_length(sys.argv, 2, "No upload config provided")
utils.verify_arg_length(sys.argv, 3, "No artifact for upload provided")

utils.verify_is_file(sys.argv[1], "Invalid config filename")
utils.verify_is_file(sys.argv[2], "Invalid artifact filename")

debug = "--debug" in sys.argv

# Save filename
config_filename = sys.argv[1]
artifact_filename = sys.argv[2]

# Read API tokens
tokens = utils.verify_schema_and_open("tokens.json", utils.TOKEN_SCHEMA)
cf_token = tokens["curseforge"]
modrinth_token = tokens["modrinth"] if "modrinth" in tokens else None

# Read mod config
# TODO froge compat
config = utils.verify_schema_and_open(config_filename, utils.CONFIG_SCHEMA)

# Read version from archive
mod_json = json.loads(zipfile.ZipFile(artifact_filename, "r").open("fabric.mod.json").read())
version = mod_json["version"]

# Read user input for this specific version
input_data = {"changelog": input("Changelog: "), "version": version}

release_type = utils.parse_release_type("Release Type: ")
while release_type not in utils.VALID_RELEASE_TYPES:
    release_type = utils.parse_release_type("Invalid type. Try again: ")

input_data["releaseType"] = release_type

# Give the option to upload to both platforms
if utils.confirm("Upload to CurseForge?"):
    host_adapters.upload_curseforge(artifact_filename, cf_token, config, input_data, debug)

if modrinth_token and "modrinth_id" in config and utils.confirm("Upload to Modrinth?"):
    host_adapters.upload_modrinth(artifact_filename, modrinth_token, config, input_data, debug)

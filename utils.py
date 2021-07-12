import os.path
import json

VALID_RELEASE_TYPES = ["alpha", "beta", "release"]
CONFIG_SCHEMA = ["display_name", "curseforge_id", "modloader", "minecraft_versions"]
TOKEN_SCHEMA = ["curseforge"]


def confirm(prompt):
    return input(prompt + " y/n \n") == "y"


def parse_release_type(prompt):
    input_type = input(prompt)
    if input_type == "r":
        input_type = "release"
    elif input_type == "a":
        input_type = "alpha"
    elif input_type == "b":
        input_type = "beta"
    return input_type


def format_version_string(mod_config, version):
    return "[" + mod_config["minecraft_versions"][0] + (
        "+] " if len(mod_config["minecraft_versions"]) > 1 else "] ") + mod_config["display_name"] + " - " + version


def verify_arg_length(args, min_length, error_message):
    if len(args) < min_length:
        print(error_message)
        exit(1)


def verify_is_file(file, error_message):
    if not os.path.isfile(file):
        print(error_message)
        exit(1)


def verify_schema_and_open(filename, required_keys):
    data = json.loads(open(filename).read())
    verify_json_schema(filename, data, required_keys)
    return data


def verify_json_schema(json_name, json, required_keys):
    for key in required_keys:
        if key not in json:
            print(json_name + " is missing required key " + key)
            exit(1)
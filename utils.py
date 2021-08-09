import json
import os.path

from termcolor import colored

VALID_RELEASE_TYPES = ["alpha", "beta", "release"]

CONFIG_SCHEMA = ["display_name", "curseforge_id", "minecraft_versions"]
ARTIFACT_SEARCH_SCHEMA = ["artifact_directory", "artifact_filename_pattern"]

TOKEN_SCHEMA = ["curseforge"]

log_action_active = False


def confirm(prompt):
    return colored_input(prompt + " ") == "y"


def parse_release_type(prompt, prompt_color="magenta"):
    input_type = colored_input(prompt, prompt_color)
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


def verify_is_file(file, error_message):
    if not os.path.isfile(file):
        fail(error_message)
        exit(1)


def verify_schema_and_open(filename, required_keys):
    data = json.loads(open(filename).read())
    verify_json_schema(filename, data, required_keys)
    return data


def verify_json_schema(json_name, json, required_keys):
    for key in required_keys:
        if key not in json:
            fail(json_name + " is missing required key " + key)
            exit(1)


def verify_file_in_zip(zipfile, mod_info_path):
    return mod_info_path in zipfile.namelist()


def fail(message, error_code=1):
    if log_action_active:
        print(colored("Failed", "red"))

    print(colored("\nThe following error has occurred:", "red"), end=" ")
    print(colored(message + "\n", "yellow"))
    if not error_code == -1:
        exit(error_code)


def log_action(message):
    global log_action_active
    print(" - " + message, end=" ... ")
    log_action_active = True


def finish_log_action():
    global log_action_active
    if log_action_active:
        print(colored("Done", "green"))
        log_action_active = False


def colored_input(message, color="magenta"):
    print(colored(message, color), end="")
    return input()


def pretty_print_property(key, value, key_color="green", padding=20):
    actual_padding = padding - len(key + ": ")
    print(colored(key + ": ", key_color) + (" " * actual_padding) + value)

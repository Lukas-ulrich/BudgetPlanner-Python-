import os
import json
import csv

DEFAULT_STRUCTURE = {
BASE_FOLDER = "profiles"
DEFAULT_PROFILE = "default"
SETTINGS_FILE = "settings.json"

def profile_folder(profile):
    return os.path.join(BASE_FOLDER, profile)

def filename_for_month(profile, ym):
    return os.path.join(profile_folder(profile), f"budget_{ym}.json")



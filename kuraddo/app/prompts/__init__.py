from main.prompts import autocomplete
from main.prompts import checkbox
from main.prompts import confirm
from main.prompts import password
from main.prompts import path
from main.prompts import rawselect
from main.prompts import select
from main.prompts import text

AVAILABLE_PROMPTS = {
    "autocomplete": autocomplete.autocomplete,
    "confirm": confirm.confirm,
    "text": text.text,
    "select": select.select,
    "rawselect": rawselect.rawselect,
    "password": password.password,
    "checkbox": checkbox.checkbox,
    "path": path.path,
    # backwards compatible names
    "list": select.select,
    "input": text.text,
    "rawlist": rawselect.rawselect,
}

def prompt_by_name(name):
    return AVAILABLE_PROMPTS.get(name)
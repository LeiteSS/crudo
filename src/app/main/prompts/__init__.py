from main.prompts import text

AVAILABLE_PROMPTS = {
    "text": text.text,

    # backwards compatible names
    "input": text.text,
}

def prompt_by_name(name):
    return AVAILABLE_PROMPTS.get(name)
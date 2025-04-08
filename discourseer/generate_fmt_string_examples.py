import os
import sys
from pydantic import BaseModel
from typing import Dict, List
import json

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from discourseer.codebook import Codebook
from discourseer import utils

codebook_name = "codebook_gaza_v2_srpen.json"
intro = f"""
# Formátovací řetězce pro vytvoření zadání modelu pro každou otázku

Tyto příklady jsou vytvořeny podle zadání v souboru {codebook_name}.
"""

text_fmt_string_description = "vložení textu článku"

def print_prompt_exmples():

    if not os.path.exists("../experiments/example"):
        raise FileNotFoundError("Directory ../experiments/example not found.")

    os.makedirs("../experiments/example/json_outputs", exist_ok=True)
    codebook_file = os.path.join("..", "codebooks", codebook_name)
    if not os.path.exists(codebook_file):
        raise FileNotFoundError(f"File {codebook_file} not found.")

    with open(codebook_file, 'r', encoding='utf-8') as f:
        codebook_json = json.load(f)
        codebook = Codebook.model_validate(codebook_json)

    print(intro)

    format_strings = codebook.get_format_strings()

    for i, key in enumerate(format_strings, start=1):
        if key == "custom_format_string":
            continue
        print(f"{i}. [{key}](#{key})")

    for key, value in format_strings.items():
        if key == "custom_format_string":
            continue
        print('')
        if key == "text":
            print(f"**{key}** ({text_fmt_string_description})")
        elif hasattr(codebook, key):
            print(f"**{key}** ({getattr(codebook, key).__doc__})")
        else:
            print(f"**{key}** (Description not available)")
        print(f'<a name="{key}"></a>')
        print('')

        if "json" in key:
            json_output = json.loads(value)
            json_output_file = f'{key}.json'
            json_link_path = os.path.join('experiments', 'example', 'json_outputs', json_output_file)
            json_output_path = os.path.join('..', json_link_path)
            utils.dict_to_json_file(json_output, json_output_path)

            print(f"viz [{json_output_file}]({json_link_path}) pro kompletní výstup")
            print(f"```json")
            print('\n'.join(value.split('\n')[:15]))
            print("...")
            print(f"```")
        else:
            print(f"```")
            if 'bulletpoints' in key:
                print('\n'.join(value.split('\n')[:10]))
                print("...")
            else:
                print(f"{value}")
            print(f"```")

    message = f'# REAMDE\n\nThese examples are generated from the codebook in the file {codebook_name}.'
    # put message in a readme file in the example directory
    with open(os.path.join('..', 'experiments', 'example', 'README.md'), 'w', encoding='utf-8') as f:
        f.write(message)

if __name__ == "__main__":
    print_prompt_exmples()

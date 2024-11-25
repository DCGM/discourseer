import os
import sys
from pydantic import BaseModel
from typing import Dict, List
import json

sys.path.append(os.path.join(os.path.dirname(__file__), "../discourseer"))
from extraction_prompts import ExtractionPrompts
import utils

intro = """
# Formátovací řetězce pro vytvoření zadání modelu pro každou otázku

Tyto příklady jsou vytvořeny podle zadání v souboru [prompt_definitions.json](experiments/example/prompt_definitions.json).

"""

format_string_descriptions = {
    "text": "vložení textu článku",
    "prompt_names": "jména otázek oddělené čárkou",
    "prompt_descriptions": "popisy otázek oddělené mezerou (popis by měla být celá věta)",
    "prompt_names_and_descriptions_colon": "jména a popisy otázek oddělené dvojtečkou",
    "prompt_names_and_descriptions_parentheses": "jména a popisy otázek oddělené závorkami",
    "single_choice_prompts": "jména otázek, kde má model vybrat právě jednu možnost (single-choice), oddělené čárkou",
    "multiple_choice_prompts": "jména otázek, kde může model vybrat více možností (multiple-choice), oddělené čárkou",
    "prompt_options": "několikařádkový seznam možností odpovědi na otázky oddělené čárkou, kde každý řádek odpovídá jedné otázce",
    "whole_prompt_info": "několikařádkový seznam informací o otázkách (jméno, single-choice/multiple-choice, popis, seznam možností) oddělené čárkou, kde každý řádek odpovídá jedné otázce",
    "prompt_json": "JSON se všemi informacemi o otázkách",
    "response_json_schema": "JSON schéma, které odpovídá formátu odpovědí modelu",
    "response_json_schema_with_options": "JSON schéma, které odpovídá formátu odpovědí modelu s definovanými možnostmi"
}

def print_prompt_exmples():

    if not os.path.exists("../experiments/example"):
        raise FileNotFoundError("Directory ../experiments/example not found.")

    os.makedirs("../experiments/example/json_outputs", exist_ok=True)
    prompts_file = os.path.join("..", "experiments", "example", "prompt_definitions.json")
    if not os.path.exists(prompts_file):
        raise FileNotFoundError(f"File {prompts_file} not found.")

    with open(prompts_file, 'r', encoding='utf-8') as f:
        prompts = json.load(f)
        prompts = ExtractionPrompts.model_validate(prompts)

    print(intro)

    format_strings = prompts.get_format_strings()

    for i, key in enumerate(format_strings, start=1):
        if key == "custom_format_string":
            continue
        print(f"{i}. [{key}](#{key})")

    for key, value in format_strings.items():
        if key == "custom_format_string":
            continue
        print('')
        print(f"**{key}** ({format_string_descriptions[key]})")
        print(f'<a name="{key}"></a>')
        print('')
        if "json" in key:
            json_output = json.loads(value)
            json_output_file = f'{key}.json'
            json_output_path = os.path.join('..', 'experiments', 'example', 'json_outputs', json_output_file)
            utils.dict_to_json_file(json_output, json_output_path)

            print(f"viz [{json_output_file}]({json_output_path}) pro kompletní výstup")
            print(f"```json")
            print('\n'.join(value.split('\n')[:15]))
            print("...")
            print(f"```")
        else:
            print(f"```")
            print(f"{value}")
            print(f"```")

if __name__ == "__main__":
    print_prompt_exmples()

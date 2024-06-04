# discourseer

## Instalace
Pro spuštění je potřeba mít nainstalovaný Python 3.8, 3.9, nebo 3.10.
```bash
pip install -r requirements.txt
```
Dále je potřeba mít nastavenou proměnnou prostředí `OPENAI_API_KEY` s klíčem pro OpenAI API nebo ho předat jako parametr při spuštění `--openai-api-key`

## Příklad spuštění
```bash
python run_discourseer.py --texts-dir data/texts-vlach --ratings-dir data/texts-vlach-ratings/ --openai-api-key sk-ZmfV3vvo19y...
```

## Popis parametrů
- `-h`, `--help` - Zobrazí nápovědu.
- `--texts-dir` (složka) - Adresář s texty, které chcete analyzovat.
- `--ratings-dir` (složka jedna nebo víc) - Adresáře s hodnoceními textů.
- `--prompt-definitions` (soubor) - Soubor s definicemi otázek, které chcete z textů extrahovat. (viz `data/default/prompt_definitions.json`)
- `--prompt-subset` - Názvy témat, které chceme vybrat ze souboru `--prompt-definitions`.
- `--prompt-schema-definition` (soubor) - Soubor s textem hlavního promptu + formátovacími řetězci pro témata. (viz `data/default/prompt_schema_definitions.json`)
- `--output-dir` (složka) - Složka, kam se uloží výsledky analýzy.
- `--openai-api-key` - Klíč pro OpenAI API.
- `--log` - Úroveň logování do terminálu. (DEBUG, INFO, WARNING, ERROR)
- `--copy-input-ratings` (možnosti: none, original, reorganized) - Kopírovat hodnocení z vstupní složky do výstupní složky.
  - `none` - Nezkopírovat.
  - `original` - Zkopírovat všechny soubory v původním formátu.
  - `reorganized` - Zkopírovat přeorganizované soubory. (mohou být smazány nepotřebné soubory)

### Formátovací řetězce
Jsou definovány v souboru `discourseer/extraction_prompts.py` a mohou být použity v souboru `data/default/prompt_schema_definitions.json`:  

- text: vložení textu článku
- prompt_names: jména otázek oddělené čárkou
- prompt_descriptions: popisy otázek oddělené mezerou (popis by měla být celá věta)
- prompt_names_and_descriptions_colon: jména a popisy otázek oddělené dvojtečkou (např. "Země": "Země původu textu.") 
- prompt_names_and_descriptions_parentheses: jména a popisy otázek oddělené závorkami (např. "Země" ("Země původu textu."))
- single_choice_prompts
- multiple_choice_prompts
- prompt_options
- whole_prompt_info
- prompt_json
- response_json_schema
- response_json_schema_with_options

## Automatické testování
```bash
python -m unittest
```
Případně jednotlivé testy pomocí:
```bash
python -m unittest test.test_IRR.test_IRR.TestIRRWithoutModel.test_irr_equal
```

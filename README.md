# Discourseer

<p align="center">
  <img src="images/Discourseer_logo.jpeg" alt="Discourseer logo" width="300"/>
</p>

<p align="center">
  *Obsahová analýza pomocí jazykových modelů a jak na to...*
</p>

Obsahová analýza dokumentů je jeden z procesů žurnalistického výzkumu. Je prováděn manuálně několika nezávislými respondenty,
kteří po přečtení textu odpovídají na otázky pomocí výběru z možností: téma článku, vystupjící mluvčí, atd. 
Mezi odpověďmi několika respondentů se následně provádí analýza podobnosti, protože ne vždy je odpověď přesně daná.
Projekt Discourseer má za cíl otestovat, zda se velké jazykové modely do tohoto procesu mohou zapojit či ho zcela nahradit.

## Funkcionalita
Nástroj Discourseer umožňuje využít velké jazykové modely pomocí openAI API pro analýzu textů a odpovídání na otázky s předdefinovanými možnostmi odpovědí.

Vstupy:

- texty k analýze
- definice otázek a možných odpovědí
- definice promptů pro modely a vybrání modelu
- předchozí odpovědi respondentů

Výstupy:
- odpovědi modelu na otázky (ve formátu CSV)
- výsledky analýzy podobnosti odpovědí modelu a respondentů pomocí Inter-rater reliability (IRR) (ve formátu JSON)

## Struktura projektu
- `run_discourseer.py` - hlavní skript pro spuštění nástroje
- `discourseer` - zdrojové kódy
- `experiments` - výsledky experimentů
  - `experiments/default_experiment` - výchozí experiment pro ukázku
- `test` - automatické testy jednotlivých modulů spustitelné pomocí `python -m unittest`

## Instalace
Pro spuštění je potřeba mít nainstalovaný Python 3.8, 3.9, nebo 3.10. Dále je potřeba nainstalovat python knihovny ze souboru `requirements` např. pomocí `pip`:
```bash
pip install -r requirements.txt
```
Dále je potřeba definovat vlastní API klíč pro OpenAI API buď jako proměnnou prostředí `OPENAI_API_KEY` nebo předat programu jako parametr `--openai-api-key`.

## Příklad spuštění
Výchozí způsob spuštění pomocí vlastního API klíče je následující: 
```bash
python run_discourseer.py --openai-api-key sk-ZmfV3vvo19y...
```

## Popis parametrů
- `-h`, `--help` - Zobrazí nápovědu.
-  `--experiment-dir` (složka) - Výchozí složka pro vstupy a výstupy experimentu. Jednotlivé cesty jdou definovat pomocí dalších argumentů.
- `--texts-dir` (složka s .txt soubory) - Adresář s texty, které chcete analyzovat.
- `--ratings-dir` (složka jedna nebo víc s .csv soubory) - Adresáře s hodnoceními textů od respondentů.
- `--prompt-definitions` (soubor .json) - Soubor s definicemi otázek, které chcete z textů extrahovat. (viz `experiments/default_experiment/prompt_definitions.json`)
- `--prompt-subset` - Názvy otázek, které se mají vybrat ze souboru `--prompt-definitions`. Ostatní nejsou brány v potaz. Pokud tento argument není zadán, berou se všechny otázky.
- `--prompt-schema-definition` (soubor .json) - Soubor s textem hlavního promptu + formátovacími řetězci pro témata. (viz `experiments/default_experiment/prompt_schema_definitions.json`)
- `--output-dir` (složka) - Složka, kam se uloží výsledky analýzy.
- `--copy-input-ratings` - Možnosti kopírovat hodnocení ze vstupní složky do výstupní složky.
  - `none` - Nezkopírovat.
  - `original` - Zkopírovat všechny soubory v původním formátu.
  - `reorganized` - Zkopírovat přeorganizované soubory na co nejmenší počet respondentů. (mohou být smazány nepotřebné soubory)
- `--openai-api-key` - Klíč pro OpenAI API.
- `--log` - Úroveň logování informací o průběhu programu do terminálu. (DEBUG, INFO, WARNING, ERROR)

### Formátovací řetězce
Pomocí formátovacích řetězců lze přesně definovat formulaci otázek pro modely a to nezávisle na konkrétní otázce.
Používají se při definici promptů v souboru `prompt_schema_definitions.json` 
(např. `experiments/default_experiment/prompt_schema_definitions.json`) a jsou definovány 
v souboru `discourseer/extraction_prompts.py`, kde jdou jednoduše přidat další podle předlohy `custom_format_string`.

Seznam implementovaných formátovacích řetězců:
- text: vložení textu článku
- prompt_names: jména otázek oddělené čárkou
- prompt_descriptions: popisy otázek oddělené mezerou (popis by měla být celá věta)
- prompt_names_and_descriptions_colon: jména a popisy otázek oddělené dvojtečkou (např. "Země": "Země původu textu.") 
- prompt_names_and_descriptions_parentheses: jména a popisy otázek oddělené závorkami (např. "Země" ("Země původu textu."))
- single_choice_prompts: jména otázek, kde má model vybrat právě jednu možnost (single-choice), oddělené čárkou
- multiple_choice_prompts: jména otázek, kde může model vybrat více možností (multiple-choice), oddělené čárkou
- prompt_options: několikařádkový seznam možností odpovědi na otázky oddělené čárkou, kde každý řádek odpovídá jedné otázce 
- whole_prompt_info: několikařádkový seznam informací o otázkách (jméno, single-choice/multiple-choice, popis, seznam možností) oddělené čárkou, kde každý řádek odpovídá jedné otázce 
- prompt_json: JSON se všemi informacemi o otázkách
- response_json_schema: JSON schéma, které odpovídá formátu odpovědí modelu
- response_json_schema_with_options: JSON schéma, které odpovídá formátu odpovědí modelu s definovanými možnostmi

## Automatické testování
```bash
python -m unittest
```
Případně jednotlivé testy pomocí zavolání konkrétní třídy a metody, např.:
```bash
python -m unittest test.test_IRR.test_IRR.TestIRRWithoutModel.test_irr_equal
```

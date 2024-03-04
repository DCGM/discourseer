# discourseer

## Instalace
Pro spuštění je potřeba mít nainstalovaný Python 3.8 a vyšší.
```bash
pip install -r requirements.txt
```
Dále je potřeba mít nastavenou proměnnou prostředí `OPENAI_API_KEY' s klíčem pro OpenAI API nebo ho předat jako parametr při spuštění `--openai-api-key`

## Příklad spuštění
```bash
python extract_topics.py --texts-dir data/texts-vlach --ratings-dir data/texts-vlach-ratings-1ofN/ --output-file data/outputs/out_test.txt --topic-subset 9-place 8-message-trigger 6-genre 5-range --openai-api-key sk-ZmfV3vvo19y...
```

## Popis parametrů
- `-h`, `--help` - Zobrazí nápovědu.
- `--texts-dir` (složka) - Adresář s texty, které chcete analyzovat.
- `--ratings-dir` (složka jedna nebo víc) - Adresáře s hodnoceními textů.
- `--topic-definitions` (soubor) - Soubor s definicemi témat, které chcete z textů extrahovat.
- `--topic-subset` - Názvy témat, které chceme vybrat ze souboru `--topic-definitions`.
- `--output-file` (soubor) - Soubor, kam se uloží výsledky analýzy.
- `--prompt-definition` (soubor) - Soubor s textem hlavního promptu + formátovacími řetězci pro témata.
- `--openai-api-key` - Klíč pro OpenAI API.
- `--log` - Úroveň logování do terminálu. (DEBUG, INFO, WARNING, ERROR)

## Automatické testování
```bash
python -m unittest
```

## TODOs:
Add inter-rater reliability analysis demo
- add support for M from N options
  - propagate extraction prompts to have all options 
- add options-aware response parsing
  - add testing suite for that... response json -> rater.ratings
- add possible response options to CAC init (for better calculation of IRR I guess...)
  - It would need to have sets of options for different questions though? (see documentation https://github.com/afergadis/irrCAC/blob/f737d4c018707df582e593943d855ecbfd5a88fd/irrCAC/raw.py#L123)
- create JSON schema for model response using dynamic pydantic models (see https://stackoverflow.com/questions/66168517/generate-dynamic-model-using-pydantic)

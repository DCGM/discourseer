# discourseer


## Instalace
Pro spuštění je potřeba mít nainstalovaný Python 3.8 a vyšší.
```bash
pip install -r requirements.txt
```
Dále je potřeba mít nastavenou proměnnou prostředí `OPENAI_API_KEY' s klíčem pro OpenAI API.

## Příklad spuštění
```bash
python extract_topics.py --texts-dir data/texts-vlach --ratings-dir data/texts-vlach-ratings-1ofN/ --output-file data/outputs/out_test.txt  --log DEBUG --extract 9-place 8-message-trigger 6-genre 5-range
```

## Popis parametrů
- `--extract` - Názvy extrakčních promptů, které chceme použít.
- `--texts-dir` - Adresář s texty, které chceme analyzovat.
- `--ratings-dir` - Adresář s hodnoceními textů.
- `--output-file` - Soubor, kam se uloží výsledky analýzy.
- `--log` - Úroveň logování do terminálu.

## TODOs:
Add inter-rater reliability analysis demo
- add support for M from N options
  - propagate extraction prompts to have all options 
- add options-aware response parsing
  - add testing suite for that... response json -> rater.ratings
- move testing code to new folder `test` and copy test data there

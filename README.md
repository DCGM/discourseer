# discourseer

## Instalace
Pro spuštění je potřeba mít nainstalovaný Python 3.8 a vyšší.
```bash
pip install -r requirements.txt
```
Dále je potřeba mít nastavenou proměnnou prostředí `OPENAI_API_KEY` s klíčem pro OpenAI API nebo ho předat jako parametr při spuštění `--openai-api-key`

## Příklad spuštění
```bash
python extract_topics.py --texts-dir data/texts-vlach --ratings-dir data/texts-vlach-ratings/ --openai-api-key sk-ZmfV3vvo19y...
```

## Popis parametrů
- `-h`, `--help` - Zobrazí nápovědu.
- `--texts-dir` (složka) - Adresář s texty, které chcete analyzovat.
- `--ratings-dir` (složka jedna nebo víc) - Adresáře s hodnoceními textů.
- `--topic-definitions` (soubor) - Soubor s definicemi témat, které chcete z textů extrahovat.
- `--topic-subset` - Názvy témat, které chceme vybrat ze souboru `--topic-definitions`.
- `--output-dir` (složka) - Složka, kam se uloží výsledky analýzy.
- `--prompt-definition` (soubor) - Soubor s textem hlavního promptu + formátovacími řetězci pro témata.
- `--openai-api-key` - Klíč pro OpenAI API.
- `--log` - Úroveň logování do terminálu. (DEBUG, INFO, WARNING, ERROR)

## Automatické testování
```bash
python -m unittest
```

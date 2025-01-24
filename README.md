# Discourseer - Obsahová analýza pomocí jazykových modelů

<p align="center">
  <img src="assets/Discourseer_logo.jpeg" alt="Discourseer logo" width="300"/>
</p>

<p align="center">
  Vojtěch Vlach, xvlach22@vutbr.cz</br>
  <a href="assets/presentation.pdf">Prezentace na závěr fáze příprav kódu.</a></br>
</p>

Obsahová analýza je jedna z technik mediálně vědného výzkumu. Je prováděna manuálně několika kodéry, 
kteří po přečtení vybraných zpravodajských textů odpovídají na otázky týkající se tématu článku, zastoupených  mluvčí, přítomných zpravodajských hodnot či mediálních rámců. 
Na základě datových matic jednotlivých kodérů se následně provádí analýza inter-rater reliability, kde koeficient (Krippendorfovo alpha, Cohennovo kappa) určí míru vzájemné shody.

**Projekt Discourseer** má za cíl otestovat, zda se velké jazykové modely mohou do procesu obsahové analýzy zapojit či  manuální kódování i zcela nahradit. 
Ve spolupráci s odborníky z oboru jsme vytvořili sadu obsahové analýzy, na které budeme testovat jazykové modely a měřit jejich úspěšnost a podobnost s reálnými respondenty.

## Obsah
1. [Současný stav](#soucasny-stav)
2. [Funkcionalita](#funkcionalita)
3. [Struktura projektu](#struktura-projektu)
4. [Instalace](#instalace)
5. [Příklad spuštění](#priklad-spusteni)
6. [Automatické testování](#automaticke-testovani)
7. [Popis parametrů](#popis-parametru)
8. [Formátovací řetězce](#formatovaci-retezce)
9. [Vytváření vlastních experimentů](#vytvareni-vlastnich-experimentu)
10. [Výstupy spuštění](#vystupy-spusteni)

## Současný stav
<a name="soucasny-stav"></a>
Momentálně je software připraven na experimenty. Data pro experimenty se připravují v rámci projektu semANT na FIT VUT a budou na téma: Obsahová analýza článků souvisejících s aktuálně probíhajícím konfliktem na blízkém východě. Připravená data a první experimenty jsou očekávány během června. Tento software se bude dále vyvíjet podle potřeb uživatelů.

## Funkcionalita
<a name="funkcionalita"></a>
Nástroj Discourseer umožňuje využít velké jazykové modely pomocí openAI API pro analýzu textů a odpovídání na otázky s předdefinovanými možnostmi odpovědí. Umožňuje výběr jedné nebo více odpovědí pro každou otázku.

**Vstupy** (detailnější popis, viz [Vytváření vlastních experimentů](#vytvareni-vlastnich-experimentu))

- články (texty) k analýze v .txt
- definice promptů pro modely a vybrání modelu v .json
- odpovědi lidských kodérů (ratings) v .csv
- definice otázek a možných odpovědí (codebook) v .json


**Výstupy**
- odpovědi modelu na otázky (ve formátu CSV)
- výsledky analýzy podobnosti odpovědí modelu a respondentů pomocí Inter-rater reliability (IRR) (ve formátu JSON)

## Struktura projektu
<a name="struktura-projektu"></a>
- `run_discourseer.py` - hlavní skript pro spuštění nástroje
- `discourseer` - zdrojové kódy
- `experiments` - výsledky experimentů
  - `experiments/default_experiment` - výchozí experiment pro ukázku
- `test` - automatické testy jednotlivých modulů spustitelné pomocí `python -m unittest`

## Instalace
<a name="instalace"></a>
Pro spuštění je potřeba mít nainstalovaný Python 3.8, 3.9, nebo 3.10. Dále je potřeba nainstalovat python knihovny ze souboru `requirements` např. pomocí `pip`:
```bash
pip install -r requirements.txt
```
Dále je potřeba definovat vlastní API klíč pro OpenAI API buď jako proměnnou prostředí `OPENAI_API_KEY` nebo předat programu jako parametr `--openai-api-key`.

## Příklad spuštění
<a name="priklad-spusteni"></a>
Výchozí způsob spuštění pomocí vlastního API klíče je následující: 
```bash
python run_discourseer.py --openai-api-key sk-ZmfV3vvo19y...
```

## Automatické testování
<a name="automaticke-testovani"></a>
```bash
python -m unittest
```
Případně jednotlivé testy pomocí zavolání konkrétní třídy a metody, např.:
```bash
python -m unittest test.test_IRR.test_IRR.TestIRRWithoutModel.test_irr_equal
```

## Popis parametrů
<a name="popis-parametru"></a>
- `-h`, `--help` - Zobrazí nápovědu.
-  `--experiment-dir` (složka) - Výchozí složka pro vstupy a výstupy experimentu. Jednotlivé cesty jdou definovat pomocí dalších argumentů.
- `--texts-dir` (složka s .txt soubory) - Adresář s texty, které chcete analyzovat.
- `--ratings-dir` (složka jedna nebo víc s .csv soubory) - Adresáře s hodnoceními textů od respondentů.
- `--prompt-definitions` (soubor .json) - Soubor s definicemi otázek, které chcete z textů extrahovat. (viz `experiments/default_experiment/prompt_definitions.json`)
- `--prompt-subset` - Názvy otázek, které se mají vybrat ze souboru `--prompt-definitions`. Ostatní nejsou brány v potaz. Pokud tento argument není zadán, berou se všechny otázky.
- `--prompt-schema-definition` (soubor .json) - Soubor s textem hlavního promptu + formátovacími řetězci pro témata. (viz `experiments/default_experiment/prompt_schema_definitions.json`)
- `--output-dir` (složka) - Složka, kam se uloží výsledky analýzy.
- `--text-count` (číslo) - Možnost omezit počet dokumentů, nad kterýmu se provede analýza
- `--copy-input-ratings` - Možnosti kopírovat hodnocení ze vstupní složky do výstupní složky.
  - `none` - Nezkopírovat.
  - `original` - Zkopírovat všechny soubory v původním formátu.
  - `reorganized` - Zkopírovat přeorganizované soubory na co nejmenší počet respondentů. (mohou být smazány nepotřebné soubory)
- `--openai-api-key` - Klíč pro OpenAI API.
- `--log` - Úroveň logování informací o průběhu programu do terminálu. (DEBUG, INFO, WARNING, ERROR)

## Formátovací řetězce
<a name="formatovaci-retezce"></a>
Pomocí formátovacích řetězců lze přesně definovat formulaci otázek pro modely a to nezávisle na konkrétní otázce.
Používají se při definici promptů v souboru `prompt_schema_definitions.json` 
(např. `experiments/default_experiment/prompt_schema_definitions.json`) a jsou definovány 
v souboru `discourseer/extraction_prompts.py`, kde jdou jednoduše přidat další podle předlohy `custom_format_string`.

Viz [format_string_examples](format_string_examples.md) pro příklady.

Seznam implementovaných formátovacích řetězců:
- `text`: vložení textu článku
- `prompt_names`: jména otázek oddělené čárkou
- `prompt_descriptions`: popisy otázek oddělené mezerou (popis by měla být celá věta)
- `prompt_names_and_descriptions_colon`: jména a popisy otázek oddělené dvojtečkou (např. "Země": "Země původu textu.") 
- `prompt_names_and_descriptions_parentheses`: jména a popisy otázek oddělené závorkami (např. "Země" ("Země původu textu."))
- `single_choice_prompts`: jména otázek, kde má model vybrat právě jednu možnost (single-choice), oddělené čárkou
- `multiple_choice_prompts`: jména otázek, kde může model vybrat více možností (multiple-choice), oddělené čárkou
- `prompt_options`: několikařádkový seznam možností odpovědi na otázky oddělené čárkou, kde každý řádek odpovídá jedné otázce
- `prompt_options_with_examples`: seznam možností jako `prompt_options` s přidanými příklady na každém řádku
`prompt_options_with_examples_bulletpoints`": seznam možností jako `prompt_options_with_examples`, strukturované pomocí odrážek
- `whole_prompt_info`: několikařádkový seznam informací o otázkách (jméno, single-choice/multiple-choice, popis, seznam možností) oddělené čárkou, kde každý řádek odpovídá jedné otázce 
`whole_prompt_info_bulletpoints`: několikařádkový seznam informací jako `whole_prompt_info`, strukturované pomocí odrážek
- `prompt_json`: JSON se všemi informacemi o otázkách
- `response_json_schema`: JSON schéma, které odpovídá formátu odpovědí modelu
- `response_json_schema_with_options`: JSON schéma, které odpovídá formátu odpovědí modelu s definovanými možnostmi


## Vytváření vlastních experimentů
<a name="vytvareni-vlastnich-experimentu"></a>

Pro vytvoření vlastního experimentu je třeba vytvořit:
* základní prompt s formátovacími řetězci, viz např. (prompt_schema_definition.json)[experiments/default_experiment/prompt_schema_definition.json]
* textové dokumenty s texty článků s názvem odpovídajícím odpovědím kodérů: `file_id.txt`
* Odpovědi kodérů po souborech pro jednotlivé kodéry (ratings) v csv formátu: `file_id,prompt_id,option_id,[option_id,...]`, kde je možnost přidat neomezeně možností na jeden řádek.
* codebook definující zkoumané otázky, jejich popis, zda je možnost vybrat více možností naráz, pro každou možnost sadu odpovědí a případně příklady možností, viz např: [Codebook ke konfilktu v Gaze v2 (srpen)](codebooks/codebook_gaza_v2_srpen.json)

### Prompt engineering
Typické využití Discourseeru může být testování různých formulací popisů otázek a možností za účelem získat co nejlepší odpovědi od chatového klienta (prompt engineering). V tomto případě většinou zůstávají **stejné texty a hodnocení kodérů** a mění se codebook (různé formulace otázek a možností). Je nutné se řídit následující tabulkou, aby Discourseer správně fungoval.

<table class="tg"><thead>
  <tr>
    <th class="tg-c3ow"><span style="font-weight:bold">Struktura codebooku</span></th>
    <th class="tg-c3ow"><span style="font-weight:bold">Vidí model</span></th>
    <th class="tg-c3ow"><span style="font-weight:bold">Můžu měnit*</span></th>
    <th class="tg-c3ow"><span style="font-weight:bold">Komentář</span></th>
  </tr></thead>
<tbody>
  <tr>
    <td class="tg-0pky">codebook_name</td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">codebook_version</td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">prompts</td>
    <td class="tg-c3ow">--</td>
    <td class="tg-c3ow">--</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">_prompt_id</td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-0pky">slouží k výběru promptů pomocí <code>--prompt-subset</code> při spuštění experimentu <br>musí zůstat stejné jako v odpovědích kodérů</td>
  </tr>
  <!-- <tr>
    <td class="tg-0pky">__question_id</td>
    <td class="tg-c3ow">NE</td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-0pky">musí zůstat stejné jako v odpovědích kodérů</td>
  </tr> -->
  <tr>
    <td class="tg-0pky">__name</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">__description</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">__multiple_choice</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">__options</td>
    <td class="tg-c3ow">--</td>
    <td class="tg-c3ow">--</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">___option_id</td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-c3ow"><span style="font-weight:bold">NE</span></td>
    <td class="tg-0pky">musí zůstat stejné jako v odpovědích kodérů</td>
  </tr>
  <tr>
    <td class="tg-0pky">____name</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">____description</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">____examples</td>
    <td class="tg-c3ow">---</td>
    <td class="tg-c3ow">---</td>
    <td class="tg-0pky"></td>
  </tr>
  <tr>
    <td class="tg-0pky">_____option_example</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-c3ow">ANO</td>
    <td class="tg-0pky"></td>
  </tr>
</tbody></table>

\* můžu měnit názvy v codebooku, bez změny odpovědí kodérů

## Výstupy spuštění
<a name="vystupy-spusteni"></a>

příklad viz [default_experiment](experiments/default_experiment/output)

* `conversation_log.json` - záznam komunikace s modelem a její konfigurace
* `dataframe.csv` - data použitá k počítání metrik úspěšnosti (odpovědi na otázky od lidských kodérů a chat klinta) v .csv ve formátu `file_id,question_id,rating,kodér1,[kodér2,...],model,majority,maj_agreement_with_model,worst_case`
  * `rating` - buď option_id, nebo "single_choice" pro otázky s výběrem jedné odpovědi
  * `kodérN` - jména kodérů a jejich odpovědi. Vybraná možnost pro otázky s výběrem jedno odpovědi, jinak True/False dané možnosti
  * `model` - odpovědi modelu
  * `majority` - většinová odpověď lidských kodérů
  * `maj_agreement_with_model` - True/False zda model souhlasí s většinou lidských kodérů
  * `worst_case` - pomocný sloupec pro výpočet odhadu potenciální nejhorší úspěšnosti modelu
* `irr_results.json` - různé metriky úspěšnosti modelu identifikované pro jednotlivé otázky pomocí `question_id`
* `irr_results.png` - vizualizace výsledků do grafu (zobrazená metrika viz nadpis)
* `logfile.log` - debugovací informace o průběhu experimentu
* `model_ratings.csv` - odpovědi modelu ve stejném formátu jako vstupní odpovědi lidských kodérů

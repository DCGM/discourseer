
# Formátovací řetězce pro vytvoření zadání modelu pro každou otázku

Tyto příklady jsou vytvořeny podle zadání v souboru [prompt_definitions.json](experiments/example/prompt_definitions.json).


1. [prompt_names](#prompt_names)
2. [prompt_descriptions](#prompt_descriptions)
3. [prompt_names_and_descriptions_colon](#prompt_names_and_descriptions_colon)
4. [prompt_names_and_descriptions_parentheses](#prompt_names_and_descriptions_parentheses)
5. [single_choice_prompts](#single_choice_prompts)
6. [multiple_choice_prompts](#multiple_choice_prompts)
7. [prompt_options](#prompt_options)
8. [whole_prompt_info](#whole_prompt_info)
9. [prompt_json](#prompt_json)
10. [response_json_schema](#response_json_schema)
11. [response_json_schema_with_options](#response_json_schema_with_options)
12. [custom_format_string](#custom_format_string)

**prompt_names** (jména otázek oddělené čárkou)
<a name="prompt_names"></a>

```
Zpravodajské hodnoty, Message, Mediální rámce
```

**prompt_descriptions** (popisy otázek oddělené mezerou (popis by měla být celá věta))
<a name="prompt_descriptions"></a>

```
Zpravodajské hodnoty se používají k výběru událostí. Hlavní téma by mělo být obsaženo už v titulku a leadu. Mediální rámce jsou způsoby, jakými média strukturovaně zpracovávají informace o tématech.
```

**prompt_names_and_descriptions_colon** (jména a popisy otázek oddělené dvojtečkou)
<a name="prompt_names_and_descriptions_colon"></a>

```
Zpravodajské hodnoty: Zpravodajské hodnoty se používají k výběru událostí.. Message: Hlavní téma by mělo být obsaženo už v titulku a leadu.. Mediální rámce: Mediální rámce jsou způsoby, jakými média strukturovaně zpracovávají informace o tématech.
```

**prompt_names_and_descriptions_parentheses** (jména a popisy otázek oddělené závorkami)
<a name="prompt_names_and_descriptions_parentheses"></a>

```
Zpravodajské hodnoty (Zpravodajské hodnoty se používají k výběru událostí.). Message (Hlavní téma by mělo být obsaženo už v titulku a leadu.). Mediální rámce (Mediální rámce jsou způsoby, jakými média strukturovaně zpracovávají informace o tématech.)
```

**single_choice_prompts** (jména otázek, kde má model vybrat právě jednu možnost (single-choice), oddělené čárkou)
<a name="single_choice_prompts"></a>

```
Message
```

**multiple_choice_prompts** (jména otázek, kde může model vybrat více možností (multiple-choice), oddělené čárkou)
<a name="multiple_choice_prompts"></a>

```
Zpravodajské hodnoty, Mediální rámce
```

**prompt_options** (několikařádkový seznam možností odpovědi na otázky oddělené čárkou, kde každý řádek odpovídá jedné otázce)
<a name="prompt_options"></a>

```
Zpravodajské hodnoty: Negativita (Zdůrazňují se negativní jevy negativní emoce.), Blízkost (Události jsou zobrazeny jako geograficky nebo kulturně blízké.), Elitní osoby (Zpráva obsahuje stanoviska lidí a organizací vnímaných jako autority)
Message: Vnitřní politika (Informuje o politickém vývoji v Izraeli nebo v Gaze.), Mezinárodní politika (Informuje o mezinárodních reakcích na konflikt.), Vojenské operace (Zpráva popisuje vojenské operace.)
Mediální rámce: Rámec konfliktu (Zpráva situaci zobrazuje jako napjatou nebo konfliktní.), Rámec budování míru (Zpráva zvýrazňuje snahy o řešení konfliktu prostřednictvím.), Humanitární rámec (Zpráva zobrazuje důsledky konfliktu pro běžný občanský život.)
```

**whole_prompt_info** (několikařádkový seznam informací o otázkách (jméno, single-choice/multiple-choice, popis, seznam možností) oddělené čárkou, kde každý řádek odpovídá jedné otázce)
<a name="whole_prompt_info"></a>

```
Zpravodajské hodnoty: multiple_choice (description: Zpravodajské hodnoty se používají k výběru událostí.) options: Negativita (Zdůrazňují se negativní jevy negativní emoce.), Blízkost (Události jsou zobrazeny jako geograficky nebo kulturně blízké.), Elitní osoby (Zpráva obsahuje stanoviska lidí a organizací vnímaných jako autority)
Message: single_choice (description: Hlavní téma by mělo být obsaženo už v titulku a leadu.) options: Vnitřní politika (Informuje o politickém vývoji v Izraeli nebo v Gaze.), Mezinárodní politika (Informuje o mezinárodních reakcích na konflikt.), Vojenské operace (Zpráva popisuje vojenské operace.)
Mediální rámce: multiple_choice (description: Mediální rámce jsou způsoby, jakými média strukturovaně zpracovávají informace o tématech.) options: Rámec konfliktu (Zpráva situaci zobrazuje jako napjatou nebo konfliktní.), Rámec budování míru (Zpráva zvýrazňuje snahy o řešení konfliktu prostřednictvím.), Humanitární rámec (Zpráva zobrazuje důsledky konfliktu pro běžný občanský život.)
```

**prompt_json** (JSON se všemi informacemi o otázkách)
<a name="prompt_json"></a>

viz [prompt_json.json](../experiments/example/json_outputs/prompt_json.json)
```json
{
  "prompts": {
    "zpravodajské-hodnoty": {
      "name": "Zpravodajské hodnoty",
      "question_id": "Zpravodajské hodnoty",
      "description": "Zpravodajské hodnoty se používají k výběru událostí.",
      "multiple_choice": true,
      "options": [
        {
          "name": "Negativita",
          "description": "Zdůrazňují se negativní jevy negativní emoce."
        },
        {
          "name": "Blízkost",
          "description": "Události jsou zobrazeny jako geograficky nebo kulturně blízké."
...
```

**response_json_schema** (JSON schéma, které odpovídá formátu odpovědí modelu)
<a name="response_json_schema"></a>

viz [response_json_schema.json](../experiments/example/json_outputs/response_json_schema.json)
```json
{
  "properties": {
    "zpravodajské-hodnoty": {
      "items": {
        "type": "string"
      },
      "title": "Zpravodajské-Hodnoty",
      "type": "array"
    },
    "message-single": {
      "title": "Message-Single",
      "type": "string"
    },
    "medialni-ramec": {
      "items": {
...
```

**response_json_schema_with_options** (JSON schéma, které odpovídá formátu odpovědí modelu s definovanými možnostmi)
<a name="response_json_schema_with_options"></a>

viz [response_json_schema_with_options.json](../experiments/example/json_outputs/response_json_schema_with_options.json)
```json
{
  "properties": {
    "Zpravodajské hodnoty": {
      "items": {
        "enum": [
          "Negativita",
          "Blízkost",
          "Elitní osoby"
        ],
        "type": "string"
      },
      "title": "Zpravodajské Hodnoty",
      "type": "array"
    },
    "Message": {
...
```

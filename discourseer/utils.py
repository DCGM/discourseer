import json
import pydantic


def pydantic_to_json_file(model: pydantic.BaseModel, file_path: str):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(model.dict(), f, ensure_ascii=False, indent=2)

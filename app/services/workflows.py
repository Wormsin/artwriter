import json
from services.gemini_api import upload_files, call_llm, upload_small_file, structured_call_llm
from services.preprompts import *
from pathlib import Path
from pydantic import BaseModel
from docx import Document
from docx.shared import Pt


class ChapterStructure(BaseModel):
    chapter_name: str
    chapter_description: str

class ChapterTextScructure(ChapterStructure):
    text: str

class ScriptStructure(BaseModel):
    serie_number: int
    serie_name: str
    content: list[ChapterStructure]

class ScenarioStructure(BaseModel):
    serie_number: int
    serie_name: str
    content: list[ChapterTextScructure]


def save_text(content, output_file):
    """Сохраняет текстовый контент в файл."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def save_json(obj, output_file):
    """Сохраняет JSON-объект в файл."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def scenario_to_docx(output_dir):
    output_path = Path(output_dir)
    input_file = f"{output_dir}/scenario.json"
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for serie in data:
        doc = Document()
        serie_title = f"{serie['serie_number']}. {serie['serie_name']}"
        doc.add_heading(serie_title, level=0)

        for chapter in serie["content"]:
            # Название главы
            doc.add_heading(chapter["chapter_name"], level=1)

            # Описание главы (курсив)
            p_desc = doc.add_paragraph()
            run_desc = p_desc.add_run(chapter["chapter_description"])
            run_desc.italic = True
            run_desc.font.size = Pt(11)

            # Основной текст (обычный)
            p_text = doc.add_paragraph(chapter["text"])
            p_text.style = "Normal"

        file_name = f"Серия_{serie['serie_number']}_{serie['serie_name'].replace(' ', '_')}.docx"
        doc.save(output_path / file_name)
        print(f"Создан файл: {file_name}")
        

def expand_database(topic_path):
    folder_path = Path(topic_path)
    folder_path_facts = folder_path / "ФАКТЫ"
    folder_path_facts.mkdir(parents=True, exist_ok=True)
    folder_path_bd = folder_path / "БД"
    output_file = folder_path_facts / "db_extension.txt"

    file_paths = [str(file.resolve()) for file in folder_path_bd.iterdir() if file.is_file()]
    uploaded_files = upload_files(file_paths)
    prompt = get_stage1_prompt()
    response = call_llm(prompt, files=uploaded_files)
    save_text(response, output_file)
    print(f"Расширенная БД сохранена в {output_file}")
    return output_file

def find_connections(topic_path):
    output_file = f"{topic_path}/ФАКТЫ/db_facts.txt"
    file_path = f"{topic_path}/ФАКТЫ/db_extension.txt"
    uploaded_files = upload_small_file(file_path)
    prompt = get_stage2_prompt()
    response = call_llm(prompt, files=uploaded_files, thinking=True)
    save_text(response, output_file)
    print(f"Гипотезы сохранены в {output_file}")
    return output_file

def check_hypotheses(topic_path):
    hypotheses_file = f"{topic_path}/ФАКТЫ/db_facts.txt"
    output_file = f"{topic_path}/ФАКТЫ/db_facts_checked.txt"
    uploaded_files = upload_small_file(hypotheses_file)
    prompt = get_stage3_prompt()
    response = call_llm(prompt, files=uploaded_files, web_search=True, thinking=True)
    save_text(response, output_file)
    print(f"Проверенные гипотезы сохранены в {output_file}")
    return output_file

def build_script_structure(topic_path, num_series):
    output_file_json = f"{topic_path}/СТРУКТУРА/script_structure.json"
    output_file_txt = f"{topic_path}/СТРУКТУРА/script_structure.txt"
    folder_path_structure = Path(topic_path)/ "СТРУКТУРА"
    folder_path_structure.mkdir(parents=True, exist_ok=True)

    folder = Path(f"{topic_path}/БД")
    file_paths = [str(file.resolve()) for file in folder.iterdir() if file.is_file()]
    file_paths.append(f"{topic_path}/ФАКТЫ/db_facts_checked.txt")

    uploaded_files = upload_files(file_paths)
    prompt = get_stage4_prompt(num_series)
    response = structured_call_llm(prompt, files=uploaded_files, structure=list[ScriptStructure])

    scripts: list[ScriptStructure] = response.parsed
    scripts = [script.model_dump() for script in scripts]
    save_json(scripts, output_file_json)
    save_text(response.text, output_file_txt)
    print(f"Структура сценария сохранена в {output_file_json}")

    '''
    output_folder = Path(f"{topic_name}/СТРУКТУРА")
    for script in scripts:
        serie_number = script["serie_number"]
        file_name = f"serie_structure_{serie_number}.json"
        file_path = output_folder / file_name
        save_json(script, file_path)
    '''
    return output_file_json

def write_script_text(topic_path, max_output_tokens=4049):
    output_file_json=f"{topic_path}/СЦЕНАРИЙ/scenario.json"
    output_file_txt=f"{topic_path}/СЦЕНАРИЙ/scenario.txt"
    folder_path_scenario = Path(topic_path)/ "СЦЕНАРИЙ"
    folder_path_scenario.mkdir(parents=True, exist_ok=True)

    #folder = Path(f"{topic_name}/БД")
    #file_paths = [str(file.resolve()) for file in folder.iterdir() if file.is_file()]
    #file_paths.append(f"{topic_name}/ФАКТЫ/db_facts_checked.txt")
    #file_paths.append(f"{topic_name}/СТРУКТУРА/script_structure.txt")

    #uploaded_files = upload_files(file_paths)
    uploaded_files = None
    prompt = get_stage5_prompt()
    response = structured_call_llm(prompt, files=uploaded_files, structure=list[ScenarioStructure], max_output_tokens=max_output_tokens)

    print(response)
    try:
        scripts: list[ScenarioStructure] = response.parsed
        scripts = [script.model_dump() for script in scripts]
        save_json(scripts, output_file_json)
        print(f"Структура сценария сохранена в {output_file_json}")
        scenario_to_docx(f"{topic_path}/СЦЕНАРИЙ")
    except TypeError as e:
        print(f"❌ Ошибка NoneType: Обнаружено, что 'response.parsed' вернул None. Запускаю сохранение сырого текста.")
        save_text(response.text, output_file_txt)
    except Exception as e:
        print(f"⚠️ Произошла другая критическая ошибка при обработке или сохранении: {e}")

    return output_file_json
import json
from services.gemini_api import upload_files, call_llm, upload_small_file, structured_call_llm
from services.preprompts import *
from pathlib import Path
from pydantic import BaseModel, Field
from docx import Document
from docx.shared import Pt
from typing import Dict, List
import uuid
import re
import os

class ChapterStructure(BaseModel):
    chapter_number: int
    chapter_name: str
    chapter_description: str

class ChapterTextScructure(ChapterStructure):
    text: str = ""

class ScriptStructure(BaseModel):
    serie_number: int
    serie_name: str
    content: list[ChapterStructure]

class ScenarioStructure(BaseModel):
    serie_number: int
    serie_name: str
    content: list[ChapterTextScructure]

class ChapterStructureID(ChapterStructure):
    chapter_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
class ScriptStructureID(ScriptStructure):
    serie_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: list[ChapterStructureID]


# --- УТИЛИТЫ ---
def save_text(content, output_file):
    """Сохраняет текстовый контент в файл."""
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)

def save_json(obj, output_file):
    """Сохраняет JSON-объект в файл."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

        

# --- ПОИСК ДОП ФАКТОВ ---
def expand_database(topic_path, llm_model_name):
    folder_path = Path(topic_path)
    folder_path_facts = folder_path / "ФАКТЫ"
    folder_path_facts.mkdir(parents=True, exist_ok=True)
    folder_path_bd = folder_path / "БД"
    output_file = folder_path_facts / "db_extension.txt"

    file_paths = [str(file.resolve()) for file in folder_path_bd.iterdir() if file.is_file()]
    uploaded_files = upload_files(file_paths)
    prompt = get_stage1_prompt()
    response = call_llm(prompt, files=uploaded_files, 
                        model_name=llm_model_name, 
                        temperature=0.2, 
                        web_search=False)
    save_text(response, output_file)
    print(f"Расширенная БД сохранена в {output_file}")
    return output_file


# --- ПОИСК НЕОЧЕВИДНЫХ СВЯЗЕЙ ---
def find_connections(topic_path, llm_model_name):
    output_folder = Path(topic_path) / "ФАКТЫ"

    folder = Path(f"{topic_path}/БД")
    file_paths = [str(file.resolve()) for file in folder.iterdir() if file.is_file()]
    uploaded_files = upload_files(file_paths)

    lens = 0
    while True:
        lens+=1
        prompt = get_stage2_prompt_main(lens_num=lens)
        if prompt:
            response = call_llm(prompt, files=uploaded_files, 
                                model_name=llm_model_name, 
                                temperature=1.5,
                                web_search=False)
            #context = response
            output_file = output_folder / f"lens_{lens}_main.txt"
            save_text(response, output_file)
            if lens == 1:
                file_paths = [f"{topic_path}/ФАКТЫ/lens_{lens}_main.txt", f"{topic_path}/ФАКТЫ/db_extension.txt"]
                uploaded_files = upload_files(file_paths)
            else:
                file_path = f"{topic_path}/ФАКТЫ/lens_{lens}_main.txt"
                uploaded_files = upload_small_file(file_path)
        else:
            output_file = output_folder / "db_facts.txt"
            save_text(response, output_file)
            break
    print(f"Гипотезы сохранены в {output_file}")
    return output_file


def find_connections_blind_spots(topic_path, llm_model_name):
    output_folder = Path(topic_path) / "ФАКТЫ"

    folder = Path(f"{topic_path}/БД")
    file_paths = [str(file.resolve()) for file in folder.iterdir() if file.is_file()]
    file_paths.append(f"{topic_path}/ФАКТЫ/db_extension.txt")
    uploaded_files = upload_files(file_paths)

    lens = 0
    while True:
        lens+=1
        prompt = get_stage2_prompt_blind_spots(lens_num=lens)
        if prompt:
            response = call_llm(prompt, files=uploaded_files, 
                                model_name=llm_model_name, 
                                temperature=1.5,
                                web_search=False)
            
            output_file = output_folder / f"lens_{lens}_blind_spots.txt"
            save_text(response, output_file)
        else:
            return output_file

# --- ПРОВЕРКА ГИПОТЕЗ ---
def extract_blocks(text, start_tag, end_tag):
    pattern = re.compile(rf"\[{start_tag}\](.*?)\[{end_tag}\]", re.DOTALL)
    return [block.strip() for block in pattern.findall(text)]
def connect_check_hypothese_results(topic_path):
    file_hypothesis = f"{topic_path}/ФАКТЫ/db_facts.txt"
    files_checks = [f"{topic_path}/ФАКТЫ/db_facts_checked_1.txt", 
                    f"{topic_path}/ФАКТЫ/db_facts_checked_2.txt", 
                    f"{topic_path}/ФАКТЫ/db_facts_checked_3.txt"]
    output_file = f"{topic_path}/ФАКТЫ/db_facts_checked.txt"
    with open(file_hypothesis, "r", encoding="utf-8") as f:
        hypotheses = extract_blocks(f.read(), "НАЧАЛО ГИПОТЕЗЫ", "КОНЕЦ ГИПОТЕЗЫ")
    all_checks = []
    for path in files_checks:
        with open(path, "r", encoding="utf-8") as f:
            checks = extract_blocks(f.read(), "НАЧАЛО ПРОВЕРКИ", "КОНЕЦ ПРОВЕРКИ")
            all_checks.append(checks)
    num_hypotheses = len(hypotheses)
    for i, checks in enumerate(all_checks, 1):
        if len(checks) != num_hypotheses:
            print(f"⚠️ Предупреждение: в файле проверки {i} найдено {len(checks)} блоков, "
                f"а гипотез — {num_hypotheses}.")
    merged_blocks = []
    for i in range(num_hypotheses):
        block = "[НАЧАЛО ПРОВЕРКИ ГИПОТЕЗЫ]\n"
        block += hypotheses[i] + "\n\n"
        # добавляем все проверки для этой гипотезы
        for checks in all_checks:
            if i < len(checks):
                block += checks[i] + "\n\n"
        block += "[КОНЕЦ ПРОВЕРКИ ГИПОТЕЗЫ]\n"
        merged_blocks.append(block)

    # --- Сохраняем результат ---
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(merged_blocks))
    for file_path in files_checks:
        if os.path.exists(file_path):
            os.remove(file_path)
            print(f"🗑️ Файл '{file_path}' удалён.")
        else:
            print(f"⚠️ Файл '{file_path}' не найден, пропускаем.")
    return True

def check_hypotheses(topic_path, llm_model_name):
    file_paths = [f"{topic_path}/ФАКТЫ/db_facts.txt"]
    uploaded_files = upload_files(file_paths)
    lens = 0
    while True:
        lens+=1
        prompt = get_stage3_prompt(lens_num=lens)
        if prompt:
            response = call_llm(prompt, files=uploaded_files, 
                                web_search=True, model_name=llm_model_name,
                                temperature=0.2)
            output_file = f"{topic_path}/ФАКТЫ/db_facts_checked_{lens}.txt"
            save_text(response, output_file)
            file_paths.append(f"{topic_path}/ФАКТЫ/db_facts_checked_{lens}.txt")
            uploaded_files = upload_files(file_paths)
            print(f"Проверенные гипотезы сохранены в {output_file}")
        else:
            break
    connect_check_hypothese_results(topic_path)
    return output_file



# --- СОЗДАНИЕ СТРУКТУРЫ СЦЕНАРИЯ ---
def build_script_structure(topic_path, num_series, llm_model_name):
    output_file_json = f"{topic_path}/СТРУКТУРА/script_structure.json"
    output_file_txt = f"{topic_path}/СТРУКТУРА/script_structure.txt"
    folder_path_structure = Path(topic_path)/ "СТРУКТУРА"
    folder_path_structure.mkdir(parents=True, exist_ok=True)

    folder = Path(f"{topic_path}/БД")
    file_paths = [str(file.resolve()) for file in folder.iterdir() if file.is_file()]
    file_paths.append(f"{topic_path}/ФАКТЫ/db_facts_checked.txt")

    uploaded_files = upload_files(file_paths)
    prompt = get_stage4_prompt(num_series)
    response = structured_call_llm(prompt, files=uploaded_files, structure=list[ScriptStructure],
                                    max_output_tokens=65536,
                                    model_name=llm_model_name,
                                    temperature=1)

    scripts: list[ScriptStructure] = response.parsed
    scripts_raw = [script.model_dump() for script in scripts]
    scripts_with_ids: List[ScriptStructureID] = [
    ScriptStructureID.model_validate(script) for script in scripts_raw]
    scripts_ids = [script.model_dump() for script in scripts_with_ids]
    save_json(scripts_ids, output_file_json)
    json_string = json.dumps(
        scripts_ids, 
        indent=2, 
        ensure_ascii=False
    )
    save_text(json_string, output_file_txt)
    print(f"Структура сценария сохранена в {output_file_json}")
    return output_file_json


# --- НАПИСАНИЕ ТЕКСТА СЦЕНАРИЯ---

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
            doc.add_heading(f"{chapter['chapter_number']}.   {chapter['chapter_name']}", level=1)

            # Описание главы (курсив)
            p_desc = doc.add_paragraph()
            run_desc = p_desc.add_run(chapter["chapter_description"])
            run_desc.italic = True
            run_desc.font.size = Pt(11)

            # Основной текст (обычный)
            p_text = doc.add_paragraph(chapter["text"])
            p_text.style = "Normal"

        file_name = f"Серия_{serie['serie_number']}.docx"
        doc.save(output_path / file_name)
        print(f"Создан файл: {file_name}")

def get_chapters_per_serie_from_file(file_path: str) -> Dict[int, int]:
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        raise FileNotFoundError(f"Файл не найден по пути: {file_path}")
    try:
        # 1. Считывание содержимого файла
        with open(file_path_obj, 'r', encoding='utf-8') as f:
            json_data_string = f.read()
        # 2. Парсинг JSON-строки в список словарей
        raw_data = json.loads(json_data_string)
        # 3. Валидация и создание объектов Pydantic
        # Если файл содержит список серий, парсим каждую
        scenario_data: list[ScenarioStructure] = [
            ScenarioStructure.model_validate(item) 
            for item in raw_data
        ]
    except (json.JSONDecodeError, ValueError) as e:
        raise ValueError(f"Ошибка валидации или некорректная структура JSON в файле: {e}")
    # 4. Расчет итогового словаря Dict[int, int]
    chapters_per_serie: Dict[int, int] = {}
    for serie in scenario_data:
        # Ключ: номер серии; Значение: длина списка content
        chapters_per_serie[serie.serie_number] = len(serie.content)
        
    return chapters_per_serie, scenario_data

def update_json_structure(topic_path):
    file_json = f"{topic_path}/СТРУКТУРА/script_structure.json"
    file_txt = f"{topic_path}/СТРУКТУРА/script_structure.txt"
    try:
        with open(file_txt, 'r', encoding='utf-8') as f:
            json_string = f.read()
    except FileNotFoundError:
        print(f"🛑 Ошибка: Файл не найден по пути: {file_txt}")
        return False
    except Exception as e:
        print(f"🛑 Ошибка чтения файла {file_txt}: {e}")
        return False
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"🛑 Ошибка: Содержимое файла '{file_txt}' не является валидным JSON.")
        print(f"Подробности ошибки: {e}")
        return False
    try:
        with open(file_json, 'w', encoding='utf-8') as f:
            json.dump(
                data, 
                f, 
                indent=2, 
                ensure_ascii=False
            )
        print(f"✅ Успех: Содержимое из '{file_txt}' сохранено и отформатировано в '{file_json}'")
        return True
    except Exception as e:
        print(f"🛑 Ошибка записи в JSON файл: {e}")
        return False

def write_script_text(topic_path, llm_model_name, temperature):
    update_json_structure(topic_path=topic_path)
    output_file_json=f"{topic_path}/СЦЕНАРИЙ/scenario.json"
    folder_path_scenario = Path(topic_path)/ "СЦЕНАРИЙ"
    folder_path_scenario.mkdir(parents=True, exist_ok=True)
    
    folder_db = Path(topic_path) / "БД"
    file_paths = [str(file.resolve()) for file in folder_db.iterdir() if file.is_file()]
    file_paths.append(f"{topic_path}/ФАКТЫ/db_facts_checked.txt")
    file_paths.append(f"{topic_path}/СТРУКТУРА/script_structure.txt")
    uploaded_files = upload_files(file_paths)
    #uploaded_files = None

    chapters_per_serie, scenario_data = get_chapters_per_serie_from_file(f"{topic_path}/СТРУКТУРА/script_structure.json")

    previous_chapter_text = ""
    for s in chapters_per_serie:
        for ch in range(1, chapters_per_serie[s]+1):
            prompt = get_stage5_prompt(ser=s, ch=ch, previous_chapter_text=previous_chapter_text)
            response = call_llm(prompt, files=uploaded_files, 
                                model_name=llm_model_name, 
                                temperature=1.3)
            for serie in scenario_data:
                if serie.serie_number == s:
                    target_serie = serie
                    break
            for chapter in target_serie.content:
                if chapter.chapter_number == ch:
                    target_chapter = chapter
                    break
            target_chapter.text = response
            previous_chapter_text = response
    
    try:
        scripts = [sd.model_dump() for sd in scenario_data]
        save_json(scripts, output_file_json)
        print(f"Структура сценария сохранена в {output_file_json}")
        scenario_to_docx(f"{topic_path}/СЦЕНАРИЙ")
    except TypeError as e:
        print(f"❌ Ошибка NoneType: Обнаружено, что 'response.parsed' вернул None. Запускаю сохранение сырого текста.")
    except Exception as e:
        print(f"⚠️ Произошла другая критическая ошибка при обработке или сохранении: {e}")

    return output_file_json

import sqlite3
import os
from flask import render_template
from pydantic import BaseModel, Field, create_model

from utils import *
from pdfs import test_if_pdf_exists
from AI_utils import *
from prompts import *

### create dynamic pydantic model
def create_pydantic_model(project_id):
    model_fields = {}
    fields = dict()
    sql = "SELECT id, name, description FROM study_fields WHERE project=?"
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(sql, (project_id,))
    rows = res.fetchall()
    for row in rows:
        field_name = f"F{row["id"]}"

        # field dictionary
        fields[field_name] = {'id': row["id"], 'name': row["name"], 'description': row["description"]}

        #model pydantic
        field_description = Field(..., description=row['name'] + ": " + row["description"])
        model_fields[field_name] = (str, field_description)

    cur.close()
    con.close()
    return create_model('FieldModel', **model_fields), fields


def build_extraction_prompt(fields, source):
    fields_bullet_list  = ""
    for e in fields.values():
        fields_bullet_list += " - " + e["name"] + "\n"

    system_prompt = """
    You are a specialist in randomized clinical trials and systematic reviews.
    extract information using only the given context and does not used your memory or your knowledge of the concerned trial.
    """

    if source == "pdf":
        prompt = prompt_template_extraction_pdf.format(fields=fields_bullet_list, context="{context}")
    else :
        prompt = prompt_template_extraction_abstract.format(fields=fields_bullet_list, context="{context}")

    return prompt, system_prompt


def AI_extraction_personalised_fields(study_id, record_id, project_id, context_source):
    #references = get_references(study_id)
    pdf_exists = test_if_pdf_exists(record_id)
    assert context_source in ["abstract", "pdf"]
    assert pdf_exists

    FieldModel, fields = create_pydantic_model(project_id)
    user_prompt, system_prompt = build_extraction_prompt(fields, context_source)

    if context_source == "pdf":
        context = get_pdf(record_id)
    else:
        context = get_abstract(record_id)

    extracted_data = invoke_llm_structured_output(system_prompt, user_prompt, context, FieldModel)

    return extracted_data


def AI_check_extraction(extracted_data, record_id):
    context = get_pdf(record_id)

    prompt_system = "Your are an expert of clinical trials and systematic reviews."

    prompt = prompt_template_extraction_checking.format(extracted_data=extracted_data, context=context)

    answer = invoke_llm_text_output("secondary", prompt, prompt_system)

    return answer


def get_AI_data_extraction(AI, study_id, record_id, project_id):
    AI_data = dict()
    context_source = "abstract" if AI == 1 else "pdf"
    data = AI_extraction_personalised_fields(study_id, record_id, project_id, context_source)
    for e in data:
        i = int(e[0][1:])
        AI_data[i] = e[1]
    return AI_data




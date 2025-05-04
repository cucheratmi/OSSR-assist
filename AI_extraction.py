import sqlite3
import os
from flask import render_template
from pydantic import BaseModel, Field, create_model

from utils import DB_PATH, get_references
from pdfs import test_if_pdf_exists
from AI_utils import *

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

        #fields dictionary
        fields[field_name] = {'id': row["id"], 'name': row["name"], 'description': row["description"]}

        #model pydantic
        field_description = Field(..., description=row['name'] + ": " + row["description"])
        model_fields[field_name] = (str, field_description)

    cur.close()
    con.close()
    return create_model('FieldModel', **model_fields), fields


def build_extraction_prompt(fields):
    prompt = "Here is an abstract of a randomized trial in the following context.\nState:\n"
    for e in fields.values():
        prompt += " - " + e["name"] + "\n"

    prompt += """
    
    CONTEXT:
    {context}
    """

    system_prompt = """
        You are a specialist in randomized clinical trials and systematic reviews.
        extract information using only the given context and does not used your memory or your knowledge of the concerned trial.
        """

    return prompt, system_prompt


def AI_extraction_personalised_fields(study_id, record_id, project_id, context_source):
    #references = get_references(study_id)
    pdf_exists = test_if_pdf_exists(record_id)
    assert context_source in ["abstract", "pdf"]
    assert pdf_exists

    FieldModel, fields = create_pydantic_model(project_id)
    user_prompt, system_prompt = build_extraction_prompt(fields)

    if context_source == "pdf":
        context = get_pdf(record_id)
    else:
        context = get_abstract(record_id)

    extracted_data = invoke_llm_structured_output(system_prompt, user_prompt, context, FieldModel)

    return extracted_data


def AI_check_extraction(extracted_data, record_id):
    context = get_pdf(record_id)

    prompt_system = "Your are an expert of clinical trials and systematic reviews."

    prompt = "Given the randomized clinical trial described in the CONTEXT below, could you check the correctness of this trial summary.\n" \
             "Please answer for each item with 'OK' if the item is correct, or 'ERROR' if it is not correct. If it is not correct, please provide the correct information for this item.\n"
    prompt += "TRIAL SUMMARY:\n" + extracted_data + "\n"
    prompt += "CONTEXT:\n" + context + "\n"

    answer = invoke_llm_text_output("secondary", prompt, prompt_system)

    return answer


################## results ##############################

def results_create_pydantic_model(project_id):
    model_outcomes = {}
    outcomes = dict()
    sql = "SELECT id, name, description FROM outcomes WHERE project=?"
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(sql, (project_id,))
    rows = res.fetchall()
    for row in rows:
        outcome_name = f"F{row["id"]}"

        outcomes[outcome_name] = {'id': row["id"], 'name': row["name"], 'description': row["description"]}

        #model pydantic
        outcome_description = Field(..., description=row['name'] + ": " + row["description"])
        model_outcomes[outcome_name] = (str, outcome_description)

    cur.close()
    con.close()
    return create_model('ResultsModel', **model_outcomes), outcomes


def results_build_prompt(results):
    prompt = ("Here is an report of a randomized trial in the following context.\n"+
              "State:\n")
    for e in results.values():
        prompt += " - " + e["name"] + "\n"

    prompt +="\nReport relative treatment effect estimation and its confidence interval. Format response as JSON string."
    prompt += """

    CONTEXT:
    {context}
    """

    print(prompt)

    system_prompt = """
        You are a specialist in randomized clinical trials and systematic reviews.
        Extract information using only the given context and does not used your memory or your knowledge of the concerned trial.
        """

    return prompt, system_prompt


def AI_results(study_id, record_id, project_id, context_source):
    pdf_exists = test_if_pdf_exists(record_id)
    assert context_source in ["abstract", "pdf"]
    assert pdf_exists

    ResultsModel, fields = results_create_pydantic_model(project_id)
    user_prompt, system_prompt = results_build_prompt(fields)

    if context_source == "pdf":
        context = get_pdf(record_id)
    else:
        context = get_abstract(record_id)

    extracted_data = invoke_llm_structured_output(system_prompt, user_prompt, context, ResultsModel)
    print(extracted_data)

    return extracted_data


import sqlite3
import os
from flask import render_template
from pydantic import BaseModel, Field, create_model

from utils import *
from pdfs import test_if_pdf_exists
from AI_utils import *
from prompts import *

class Extracted_Data(BaseModel):
    extracted_value: str = Field(description="extracted value")
    source: str = Field(description="source of the extracted value")
    field_name: str = Field(description="name of the field")

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
        #model_fields[field_name] = (str, field_description)
        model_fields[field_name] = (Extracted_Data, field_description)

    cur.close()
    con.close()
    return create_model('FieldModel', **model_fields), fields


def AI_extraction_personalised_fields(study_id, record_id, project_id, context_source):
    #references = get_references(study_id)
    pdf_exists = test_if_pdf_exists(record_id)
    assert context_source in ["abstract", "pdf"]
    assert pdf_exists

    FieldModel, fields = create_pydantic_model(project_id)
    fields_bullet_list  = ""
    field_names = dict()
    for e in fields.values():
        fields_bullet_list += " - " + e["name"] + "\n"
        field_names[e["id"]] = e["name"]
    parameters={'fields': fields_bullet_list}

    json_template = '{'
    for e in fields.values():
        json_template += '"' + e["name"] + '": "extracted value", '
    json_template += '}'
    parameters['json_template'] = json_template

    if context_source == "pdf":
        #context = get_pdf(record_id)
        template_name = "extraction_pdf"
        extracted_data = invoke_llm_PDF_structured_output(template_name,parameters, record_id, FieldModel)
    else:
        context = get_abstract(record_id)
        template_name = "extraction_abstract"
        extracted_data = invoke_llm_structured_output(template_name,parameters, context, FieldModel)

    AI_data = dict()
    for e in extracted_data:
        field_id = int(e[0][1:])
        AI_data[field_id] = {'extracted_value':e[1].extracted_value, 'source':e[1].source, 'field_name': field_names[field_id] }

    return AI_data

#### llamaindex extract

def llamaindexextract_field_extraction(study_id, record_id, project_id):
    model_fields = {}
    fields = dict()
    field_names= dict()
    sql = "SELECT id, name, description FROM study_fields WHERE project=?"
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(sql, (project_id,))
    rows = res.fetchall()
    for row in rows:
        field_name = f"F{row["id"]}"
        field_names[row["id"]] = row["name"]
        fields[field_name] = {'id': row["id"], 'name': row["name"], 'description': row["description"]}
        field_description = Field(..., description=row['name'] + ": " + row["description"])
        model_fields[field_name] = (str, field_description)
    cur.close()
    con.close()

    FieldModel = create_model('FieldModel', **model_fields)

    extracted_data = llamaindex_extract(record_id, FieldModel)

    for k,v in extracted_data.items():
        extracted_data[k]['field_name'] = field_names[k]

    return extracted_data


def llamaindex_extract(record_id, Pydantic_model):

    pdf_path = os.path.join(PDF_UPLOAD_PATH, f"r{record_id}.pdf")

    from llama_cloud.types import ExtractConfig, ExtractMode
    from llama_cloud_services import LlamaExtract

    llama_extract = LlamaExtract()

    try:
        # Essayer d'abord de récupérer un agent existant
        agent = llama_extract.get_agent(name="RCT_extract")
    except Exception:
        # Si l'agent n'existe pas, en créer un nouveau
        config = ExtractConfig(use_reasoning=True,
                               cite_sources=True,
                               extraction_mode=ExtractMode.MULTIMODAL)
        agent = llama_extract.create_agent(name="RCT_extract",
                                           data_schema=Pydantic_model,
                                           config=config)

    filing_info = agent.extract(pdf_path)

    print(filing_info.data)

    AI_data = dict()
    for k,v in filing_info.data.items():
        field_id = int(k[1:])
        AI_data[field_id] = {'extracted_value':v, 'source':'', 'field_name': '' }

    for k, v in filing_info.extraction_metadata['field_metadata'].items():
        field_id = int(k[1:])
        s = ""
        s+= f"Reasoning: {v["reasoning"]} <br/>"
        for e in v["citation"]:
            s += f" - page {e['page']}: {e['matching_text']} <br/>"

        AI_data[field_id]['source'] = s

    return AI_data


#### JSON ###########

def get_fields_json_template(project_id):
    sql = "SELECT id, name, description FROM study_fields WHERE project=?"
    rows = sql_select_fetchall(sql, (project_id,))

    fields_bullet_list  = ""
    for e in rows:
        fields_bullet_list += " - " + e["name"] + " (" + e["description"] + ")\n"

    json_template = '{'
    for e in rows:
        json_template += '"' + e["name"] + '": {"extracted value": "extracted value", "source": "source for the extracted value"}, '
    json_template += '}'

    fields_ids=dict()
    for e in rows:
        fields_ids[e["name"]] = e["id"]

    return fields_bullet_list, json_template, fields_ids





####################



# def pdf_extraction_anthropic_labs(study_id, record_id, project_id):
#     FieldModel, fields = create_pydantic_model(project_id)
#     fields_bullet_list  = ""
#     fields_id = dict()
#     for e in fields.values():
#         fields_bullet_list += " - " + e["name"] + " (" + e["description"] + ")\n"
#         fields_id[e["name"]] = e["id"]
#
#     j = "["
#     for e in fields.values():
#         j += "{'name':'" + e["name"] + "', 'value': 'extracted value'},"
#     j += "]"
#
#     j = '{'
#     for e in fields.values():
#         j += '"' + e["name"] + '": "extracted value", '
#     j += '}'
#
#     prompt = "Please extract the following informations:\n" + fields_bullet_list + \
#     "\nGive me a JSON file with strictly the following format: " + j
#
#     r = invoke_anthropic_llm_PDF_text_output_dev(prompt, "", record_id)
#
#     data = json.loads(r)
#     print(data)
#     print(json.dumps(data, indent=2, ensure_ascii=False))
#
#     AI_data = dict()
#     for k,v in data.items():
#         AI_data[fields_id[k]] = {'extracted_value':v, 'source':''}
#
#     return AI_data
#

def AI_check_extraction(extracted_data, record_id):
    parameters = {'extracted_data': extracted_data}
    answer = invoke_llm_PDF_text_output("secondary", "extraction_checking", parameters, record_id)
    return answer


def get_AI_data_extraction(AI, study_id, record_id, project_id, model=None):
    context_source = "abstract" if AI == 1 else "pdf"
    if model is None:
        llm_name = current_app.config['LLM_NAME']
    else :
        llm_name = model

    if llm_name == LLM_Name_Enum.ANTHROPIC.value and context_source == "pdf":
        # AI_data = pdf_extraction_anthropic_labs(study_id, record_id, project_id) # experimental à détruire
        AI_data = get_AI_data_extraction_json(study_id, record_id, project_id, llm_name)

    elif llm_name == LLM_Name_Enum.MISTRAL.value and context_source == "pdf":
        AI_data = get_AI_data_extraction_json(study_id, record_id, project_id,llm_name)

    else:
        AI_data = AI_extraction_personalised_fields(study_id, record_id, project_id, context_source)

    return AI_data


def get_AI_data_extraction_json(study_id, record_id, project_id, llm_name):
    fields_bullet_list, json_template, field_ids = get_fields_json_template(project_id)

    if llm_name == LLM_Name_Enum.OPENAI.value:
        json_template = openai_extraction_json_schema(project_id)

    parameters = {'fields': fields_bullet_list, 'json_template': json_template}

    j = invoke_llm_PDF_json_output("extraction_json", parameters, record_id, llm_name)

    AI_data = dict()
    for k,v in j.items():
        field_id = field_ids[k]
        AI_data[field_id] = {'extracted_value': v['extracted value'], 'source': v['source'], 'field_name': k}

    return AI_data

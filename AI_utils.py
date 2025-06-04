import os
from enum import Enum
from flask import current_app, Flask, session

from utils import *

from AI_mistral import *
from AI_anthropic import *
from AI_openai import *
from AI_hyperbolicxyz import *

class LLM_Name_Enum(Enum):
    MISTRAL = "mistral"
    ANTHROPIC = "claude"
    OPENAI = "openai"
    DEEPSEEK = "hyperbolic"
    LLAMAINDEX_EXTRACT = "llamaindex_extract"


#### initialisation LLM model

def initialise_LLM_model(llm_name):
    model = None
    try:
        if llm_name==LLM_Name_Enum.ANTHROPIC.value and "ANTHROPIC_API_KEY" in os.environ:
            model = ChatAnthropic(model='claude-3-7-sonnet-latest')

        elif llm_name==LLM_Name_Enum.OPENAI.value and "OPENAI_API_KEY" in os.environ:
            model = ChatOpenAI(model="gpt-4o", temperature=0)

        elif llm_name==LLM_Name_Enum.MISTRAL.value and "MISTRAL_API_KEY" in os.environ:
            model = ChatMistralAI(model="mistral-large-latest")
        else:
            model = None
            print("no model available")
    except Exception as e:
        print("erreur initialisation model")
        print(e)

    return model


def AI_initilization(app):
    llm_name = app.config['LLM_NAME']
    model = initialise_LLM_model(llm_name)
    app.config["model"] = model

    secondary_model_name = app.config['SECONDARY_LLM_NAME'] if app.config["SECONDARY_LLM_NAME"].strip()!="" else llm_name
    secondary_model = initialise_LLM_model(secondary_model_name)
    app.config["secondary_model"] = secondary_model




######## invoke llm with structured output ####################################

def invoke_llm_structured_output(template_name, parameters, context, pydantic_class):
    llm_name = current_app.config["LLM_NAME"]
    print(f"invoke_llm_structured_output, {llm_name=}")

    match llm_name:
        case LLM_Name_Enum.MISTRAL.value:
            return invoke_mistral_llm_structured_output(template_name, parameters, context, pydantic_class)
        case LLM_Name_Enum.ANTHROPIC.value:
            return invoke_anthropic_llm_structured_output(template_name, parameters, context, pydantic_class)
        case LLM_Name_Enum.OPENAI.value:
            return invoke_openai_llm_structured_output(template_name, parameters, context, pydantic_class)
        case LLM_Name_Enum.DEEPSEEK.value:
            return invoke_hyperbolic_llm_structured_output(template_name, parameters, context, pydantic_class)
        case _:
            print("no model available for structured output")
            return None


def invoke_llm_PDF_structured_output(template_name, parameters, record_id, pydantic_class):
    llm_name = current_app.config["LLM_NAME"]
    print(f"invoke_llm_PDF_structured_output, {llm_name=}")

    match llm_name:
        case LLM_Name_Enum.MISTRAL.value:
            return invoke_mistral_llm_PDF_structured_output(template_name, parameters, record_id, pydantic_class)
        case LLM_Name_Enum.OPENAI.value:
            return invoke_openai_llm_PDF_structured_output(template_name, parameters, record_id, pydantic_class)
        case LLM_Name_Enum.ANTHROPIC.value:
            return invoke_anthropic_llm_PDF_structured_output(template_name, parameters, record_id, pydantic_class)
        case LLM_Name_Enum.DEEPSEEK.value:
            return invoke_hyperbolic_llm_PDF_structured_output(template_name, parameters, record_id, pydantic_class)
        case _:
            print("no model available for structured output")
            return None

def invoke_llm_PDF_json_output(template_name, parameters, record_id, llm_name):
    print(f"invoke_llm_PDF_json_output, {llm_name=}")

    match llm_name:
        case LLM_Name_Enum.MISTRAL.value:
            return invoke_mistral_llm_PDF_json_output(template_name, parameters, record_id)
        case LLM_Name_Enum.OPENAI.value:
            return invoke_openai_llm_PDF_json_output(template_name, parameters, record_id)
        case LLM_Name_Enum.ANTHROPIC.value:
            return invoke_anthropic_llm_PDF_json_output(template_name, parameters, record_id)
        case LLM_Name_Enum.DEEPSEEK.value:
            return invoke_hyperbolic_llm_PDF_json_output(template_name, parameters, record_id)
        case _:
            print("no model available for structured output")
            return None


######## invoke llm with text output ####################################

def invoke_llm_text_output(model_level, template_name, parameters, context):
    if model_level=="secondary":
        llm_name = current_app.config["SECONDARY_LLM_NAME"]
    else:
        llm_name = current_app.config["LLM_NAME"]
    print(f"invoke_llm_text_output, {llm_name=}")

    match llm_name:
        case LLM_Name_Enum.MISTRAL.value:
            answer = invoke_mistral_llm_text_output(template_name, parameters, context)
        case LLM_Name_Enum.OPENAI.value:
            answer = invoke_openai_llm_text_output(template_name, parameters, context)
        case LLM_Name_Enum.DEEPSEEK.value:
            answer = invoke_hyperbolic_llm_text_output(template_name, parameters, context)
        case LLM_Name_Enum.ANTHROPIC.value:
            answer = invoke_anthropic_llm_text_output(template_name, parameters, context)
        case _:
            print("no model available for text output")
            answer = None

    return answer


def invoke_llm_PDF_text_output(model_level, template_name, parameters, record_id):
    if model_level=="secondary":
        llm_name = current_app.config["SECONDARY_LLM_NAME"]
    else:
        llm_name = current_app.config["LLM_NAME"]
    print(f"invoke_llm_PDF_text_output, {llm_name=}")

    match llm_name:
        case LLM_Name_Enum.MISTRAL.value:
            return invoke_mistral_llm_PDF_text_output(template_name, parameters, record_id)
        case LLM_Name_Enum.OPENAI.value:
            return invoke_openai_llm_PDF_text_output(template_name, parameters, record_id)
        case LLM_Name_Enum.ANTHROPIC.value:
            return invoke_anthropic_llm_PDF_text_output(template_name, parameters, record_id)
        case LLM_Name_Enum.DEEPSEEK.value:
            return invoke_hyperbolic_llm_PDF_text_output(template_name, parameters, record_id)
        case _:
            print("no model available for PDF output")
            return None




##############

def is_API_KEY_available(llm_name):
    if llm_name == LLM_Name_Enum.OPENAI.value:
        if "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"]!="": return True

    elif llm_name == LLM_Name_Enum.ANTHROPIC.value:
        if "ANTHROPIC_API_KEY" in os.environ and os.environ["ANTHROPIC_API_KEY"] != "": return True

    elif llm_name == LLM_Name_Enum.DEEPSEEK.value:
        if "HYPERBOLIC_API_KEY" in os.environ and os.environ["HYPERBOLIC_API_KEY"] != "": return True

    elif llm_name == LLM_Name_Enum.MISTRAL.value:
        if "MISTRAL_API_KEY" in os.environ and os.environ["MISTRAL_API_KEY"] != "": return True

    return False

def is_primary_LLM_available():
    if current_app.config["LLM_NAME"] is None or current_app.config["LLM_NAME"].strip()=="": return False
    llm_name = current_app.config["LLM_NAME"]
    if is_API_KEY_available(llm_name): return True
    return False

def is_secondary_LLM_available():
    if current_app.config["SECONDARY_LLM_NAME"] is None or current_app.config["SECONDARY_LLM_NAME"].strip()=="": return False
    llm_name = current_app.config["SECONDARY_LLM_NAME"]
    if is_API_KEY_available(llm_name): return True
    return False



def llamaindex_extract(record_id, agent_name, Pydantic_model):

    pdf_path = os.path.join(PDF_UPLOAD_PATH, f"r{record_id}.pdf")

    from llama_cloud.types import ExtractConfig, ExtractMode
    from llama_cloud_services import LlamaExtract

    llama_extract = LlamaExtract()

    try:
        # Essayer d'abord de récupérer un agent existant
        agent = llama_extract.get_agent(name=agent_name)
    except Exception:
        # Si l'agent n'existe pas, en créer un nouveau
        config = ExtractConfig(use_reasoning=True,
                               cite_sources=True,
                               extraction_mode=ExtractMode.MULTIMODAL)
        agent = llama_extract.create_agent(name=agent_name,
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
        s+= f"Reasoning: {v['reasoning']} <br/>"
        for e in v["citation"]:
            s += f" - page {e['page']}: {e['matching_text']} <br/>"

        AI_data[field_id]['source'] = s

    return AI_data


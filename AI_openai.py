import openai
from utils import *
from flask import current_app

from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate


prompt_systems_openai = {
    'screening_abstract': "Your are an expert in clinical trials and systematic review.",
    'screening_pdf': "Your are an expert in clinical trials and systematic review.",
    'extraction_abstract': """
        You are a specialist in randomized clinical trials and systematic reviews.
        extract information using only the given context and does not used your memory or your knowledge of the concerned trial.
        """,
    'extraction_pdf': """
        You are a specialist in randomized clinical trials and systematic reviews.
        extract information using only the given context and does not used your memory or your knowledge of the concerned trial.
        """,
    'extraction_checking': """
        You are a specialist in randomized clinical trials and systematic reviews.
        Check provided data using only the given context and does not used your memory or your knowledge of the concerned trial.
        """,
    'ROB_RCT': "Your are an expert in clinical trials and systematic review.",
    'ROB_checking_RCT': "Your are an expert in clinical trials and systematic review.",
    'ROB_DIAG': "Your are an expert in clinical trials and systematic review.",
    'ROB_checking_DIAG': "Your are an expert in clinical trials and systematic review.",
    'outcomes': """
        You are a specialist in randomized clinical trials and systematic reviews.
        extract information using only the given context and does not used your memory or your knowledge of the concerned trial.
        """,
    'outcomes_checking': """
        You are a specialist in randomized clinical trials and systematic reviews.
        Check provided data using only the given context and does not used your memory or your knowledge of the concerned trial.
        """,
    'chat_with_paper' : "you are an expert in clinical trial and biostatistics.",
}


prompt_template_openai = {
    'screening_abstract': """
Check if the study described in the abstract below met all the following criteria: 
{eligibility_criteria}

Start your response by 'Study is eligible' if all criteria are clearly met, or by 'Study is not eligible' if one of them is clearly not meet. 
Otherwise, start by "Eligibility unclear". Then justify your assessment.

ABSTRACT: 
{context}
""",

    ####################    

    'screening_pdf': """
Check if the study described in the context below met all the following criteria: 
{eligibility_criteria}

Start your response by 'Study is eligible' if all criteria are clearly met, or by 'Study is not eligible' if one of them is clearly not meet. 
Otherwise, start by "Eligibility unclear". Then justify your assessment.

CONTEXT: 
{context}
""",

    ####################    

    'extraction_abstract': """
Here is an abstract of a randomized trial in the following context.
Please extract the following informations and cite the text fragment you used as source:
{fields}

CONTEXT:
{context}
""",

    ####################    

    'extraction_pdf': """
Here is a fulltext report of a randomized trial in the following context.
Please extract the following informations and cite the text fragment you used as source:
{fields}

CONTEXT:
{context}
""",

#################

    'extraction_json': """Here is a fulltext report of a randomized trial in the following context.
Please extract the following informations and cite the text part you used as source:
{fields}

base64 CONTEXT:
{context}
""",

    ####################    

    'extraction_checking': """
Given the randomized clinical trial described in the CONTEXT below, could you check the correctness of this trial summary.
Please answer for each item with 'OK' if the item is correct, or 'ERROR' if it is not correct. If it is not correct, please provide the correct information for this item.

TRIAL SUMMARY:
{extracted_data}

CONTEXT:
{context}
""",

    ####################    

    'ROB_RCT': """
Here is an article reporting a randomized clinical trial in the following context.
using the ROB2.0 tools, assess and justify the risk of bias on the five ROB2.0 key domain:
 - Bias arising from the randomization process
 - Bias due to deviations from intended interventions
 - Bias due to missing outcome data
 - Bias in measurement of the outcome
 - Bias in selection of the reported result

 CONTEXT:
 {context}
""",

    ####################    

    'ROB_checking_RCT': """
Given the randomized clinical trial described in the CONTEXT below, could you check the correctness of this risk of bias assessment.
Please answer for each item with 'OK' if the item is correct, or 'ERROR' if it is not correct. If it is not correct, please provide the correct information for this item.

RISK OF BIAS ASSESSMENT
{extracted_data}

CONTEXT:
{context}
""",

    ####################    

    'ROB_DIAG': """"
Here is an article reporting a diagnostic accuracy study in the following context.
Using the QUADAS-2 tools, assess and justify the risk of bias on the seven QUADAS-2 key domain:   
 - Bias patient selection
 - Applicability patient selection
 - Bias index test(s)
 - Applicability index test(s)
 - Bias in reference standard
 - Applicability reference standard
 - Bias flow and timing

 CONTEXT:
 {context}
""",

    ####################    

    'ROB_checking_DIAG': """
Given the diagnostic accuracy study described in the CONTEXT below, could you check the correctness of this risk of bias assessment.
Please answer for each item with 'OK' if the item is correct, or 'ERROR' if it is not correct. If it is not correct, please provide the correct information for this item.

RISK OF BIAS ASSESSMENT:
{extracted_data}

CONTEXT:
{context} 
""",

    ####################    

    'outcomes': """
Here is an report of a randomized trial in the following context.

For each of the following outcomes, state the estimation of the treatment effect (Hazard ratio, odds ratio, relative risk, etc.), the lower and upper limites of its confidence interval,
the number of events in the experimental groupe, the effective of the experimental group, the number of events in the control groups, the effective of the control groups, 
the median and its confidence interval in the experimental and control groups.
Give also a short literal summary of the result.

Outcomes:
{outcomes_list}

CONTEXT:
{context}
""",

    ####################

    'results_json': """Please extract the results for the following outcomes and cite the text extract you used as source:
{outcomes_list}
    Give me a JSON file with strictly the following format: {json_template}
""",

    ####################    

    'outcomes_checking': """
Given the randomized clinical trial described in the CONTEXT below, could you check the correctness of this trial results summary.
Please answer for each item with 'OK' if the item is correct, or 'ERROR' if it is not correct. If it is not correct, please provide the correct information for this item.

TRIAL RESULTS SUMMARY:
{extracted_data}

CONTEXT:
{context}
""",

    #######################

    'chat_with_paper': """About the clinical trial described in CONTEXT, answer the following question:
{question}

CONTEXT:
{context}
"""

}


##### convenience functions #########

def invoke_openai_llm_text_output(template_name, parameters, context):
    parameters.update({'context': context})
    prompt_template = prompt_template_openai[template_name]
    prompt = prompt_template.format(**parameters)

    prompt_system = prompt_systems_openai[template_name]

    client = OpenAI()
    response = client.responses.create(
        model="gpt-4.1",
        input= prompt_system + "\n" + prompt
    )
    answer = response.output_text
    answer += "\n\n[Generated by OpenAI GPT-4.1 model]"
    return answer


def invoke_openai_llm_structured_output(template_name, parameters, context, pydantic_class):
    parameters.update({'context': context})
    prompt_template = prompt_template_openai[template_name]
    prompt = prompt_template.format(**parameters)

    prompt_system = prompt_systems_openai[template_name]

    model = current_app.config["model"]
    if model is None: return None

    prompt_template2 = ChatPromptTemplate([
        ("system", prompt_system),
        ("user", prompt)
    ])

    structured_llm = model.with_structured_output(pydantic_class)
    prompt = prompt_template2.invoke({"context": context})
    r = structured_llm.invoke(prompt)

    return r



def invoke_openai_llm_PDF_text_output(prompt_name, parameters, record_id):
    context = get_pdf(record_id)
    return invoke_openai_llm_text_output(prompt_name, parameters, context)

def invoke_openai_llm_PDF_structured_output(prompt_name, parameters, record_id, pydantic_class):
    context = get_pdf(record_id)
    return invoke_openai_llm_structured_output(prompt_name, parameters, context, pydantic_class)



def invoke_openai_llm_PDF_json_output(template_name, parameters, record_id):
    import base64
    pdf_name = f"r{record_id}.pdf"
    pdf_path = os.path.join(PDF_UPLOAD_PATH, pdf_name)

    with open(pdf_path, "rb") as pdf_file:
        binary_data = pdf_file.read()
        base64_encoded_data = base64.standard_b64encode(binary_data)
        base64_string = base64_encoded_data.decode("utf-8")

    prompt_template = prompt_template_openai[template_name]
    prompt_user = prompt_template.format(fields=parameters['fields'], context=base64_string ).strip()

    schema = json.loads(parameters['json_template'])

    client = OpenAI()
    response = client.responses.parse(
        model="gpt-4.1",
        input=[
            {
                "role": "system",
                "content": "You are an expert at structured data extraction and you give your answer in JSON format.",
            },
            {"role": "user", "content": prompt_user},
        ],
        text={ "format": { "name":"RCT_extraction", "type": "json_schema", "schema": schema, "strict": True } },
    )

    print(response.output_text)

    return json.loads(response.output_text)


def openai_extraction_json_schema(project_id):
    sql = "SELECT id, name, description FROM study_fields WHERE project=?"
    rows = sql_select_fetchall(sql, (project_id,))

    json_schema = ''
    for e in rows:
        json_schema += '"' + e["name"] + '": {"type": "string", "description": "' + e["description"] + '"}, '

    json_schema = '{ "type": "object", "properties": { ' + json_schema + '}, "required": "allOf", "additionalProperties": False }'
    return json_schema






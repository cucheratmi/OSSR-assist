from AI_utils import get_pdf
from flask import current_app
from utils import *



prompt_systems_hyperbolic = {
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
}



prompt_template_hyperbolic = {
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
State:
{fields}

CONTEXT:
{context}
""",

    ####################    

    'extraction_pdf': """
Here is a fulltext report of a randomized trial in the following context.
State:
{fields}

CONTEXT:
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
the number of events in the experimental groupe, the effective of the experimental group, the number of events in the control groups, the effective of the control groups.
Give also a short literal summary of the result.

Outcomes:
{outcomes_list}

CONTEXT:
{context}
""",

    ####################    

    'outcomes_checking': """
Given the randomized clinical trial described in the CONTEXT below, could you check the correctness of this trial results summary.
Please answer for each item with 'OK' if the item is correct, or 'ERROR' if it is not correct. If it is not correct, please provide the correct information for this item.

TRIAL RESULTS SUMMARY:
{extracted_data}

CONTEXT:
{context}
"""
}


##### convenience functions #########

def invoke_hyperbolic_llm_text_output(template_name, parameters, context):
    parameters.update({'context': context})
    prompt_template = prompt_template_hyperbolic[template_name]
    prompt = prompt_template.format(**parameters)

    prompt_system = prompt_systems_hyperbolic[template_name]

    import openai
    client = openai.OpenAI(
        api_key=os.environ["HYPERBOLIC_API_KEY"],
        base_url="https://api.hyperbolic.xyz/v1",
    )
    chat_completion = client.chat.completions.create(
        model="deepseek-ai/DeepSeek-R1",
        messages=[
            {"role": "system", "content": prompt_system},
            {"role": "user", "content": prompt},
        ],
        temperature=1,
        max_tokens=1024,
    )
    answer = chat_completion.choices[0].message.content
    answer += "\n\n[Generated by deepseek-ai/DeepSeek-V3 model]"
    return answer


def invoke_hyperbolic_llm_structured_output(template_name, parameters, context, pydantic_class):
    parameters.update({'context': context})
    prompt_template = prompt_template_hyperbolic[template_name]
    prompt = prompt_template.format(**parameters)

    prompt_system = prompt_systems_hyperbolic[template_name]

    response = ""
    return response



def invoke_hyperbolic_llm_PDF_text_output(prompt_name, parameters, record_id):
    context = get_pdf(record_id)
    return invoke_hyperbolic_llm_text_output(prompt_name, parameters, context)

def invoke_hyperbolic_llm_PDF_structured_output(prompt_name, parameters, record_id, pydantic_class):
    context = get_pdf(record_id)
    return invoke_hyperbolic_llm_structured_output(prompt_name, parameters, context, pydantic_class)






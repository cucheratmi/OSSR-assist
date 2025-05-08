
from utils import *

def get_prompt_screening(project_id, source):
    sql = "SELECT eligibility_criteria FROM projects WHERE id=?"
    eligibility_criteria = sql_select_fetchone(sql, (project_id,))['eligibility_criteria']

    prompt_template_abstract = """
    Check if the study described in the abstract below met all the following criteria: 
    {eligibility_criteria}

    Start your response by 'Study is eligible' if all criteria are clearly met, or by 'Study is not eligible' if one of them is clearly not meet. 
    Otherwise, start by "Eligibility unclear". Then justify your assessment.

    ABSTRACT: 
    """

    prompt_template_pdf = """
    Check if the study described in the context below met all the following criteria: 
    {eligibility_criteria}

    Start your response by 'Study is eligible' if all criteria are clearly met, or by 'Study is not eligible' if one of them is clearly not meet. 
    Otherwise, start by "Eligibility unclear". Then justify your assessment.

    CONTEXT: 
    """

    if source == "pdf":
        prompt =  prompt_template_pdf.format(eligibility_criteria=eligibility_criteria)
    else:
        prompt = prompt_template_abstract.format(eligibility_criteria=eligibility_criteria)

    return prompt

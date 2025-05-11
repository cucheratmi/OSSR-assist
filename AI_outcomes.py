from pydantic import BaseModel, Field, create_model

from utils import *
from pdfs import test_if_pdf_exists
from AI_utils import *
from prompts import *



########### outcomes 2 #####################################


class Result(BaseModel):
    outcome_id: int = Field(description="id of the outcome given in the prompt")
    paper_endpoint_name: str = Field(description="the name of the endpoint used in the trial report given in the CONTEXT")
    hazard_ratio: float = Field(description="hazard ratio obtained on this endpoint (point estimate)")
    ll : float = Field(description="lower limit of the confidence interval corresponding to this result")
    ul : float = Field(description="upper limit of the confidence interval corresponding to this result")
    p_value: str = Field(description="p value of the result")
    literal_summary: str = Field(description="short literal summary of the result")

class ResultsModel2(BaseModel):
    r: list[Result] = Field(description="list of the results")


def AI_results2(study_id, record_id, project_id, context_source):
    # TODO modif en cours
    pdf_exists = test_if_pdf_exists(record_id)
    assert context_source in ["abstract", "pdf"]
    assert pdf_exists

    sql = "SELECT id, name, description FROM outcomes WHERE project=?"
    r = sql_select_fetchall(sql, (project_id,))
    outcomes_list = ""
    for o in r:
        outcome = o['name'] + " (" + o['description'] + "), id:" + str(o['id'])
        outcomes_list += " - " + outcome + "\n"

    parameters = {'outcomes_list': outcomes_list}

    if context_source == "pdf":
        context = get_pdf(record_id)
    else:
        context = get_abstract(record_id)

    extracted_data = invoke_llm_structured_output("outcomes", parameters, context, ResultsModel2)

    AI_data = dict()
    for o in extracted_data.r:
        r = vars(o)
        outcome_id = int(r["outcome_id"])
        AI_data[outcome_id] = r

    return AI_data


def AI_check_outcomes(extracted_data, record_id):
    parameters = {'extracted_data': extracted_data}
    answer = invoke_llm_PDF_text_output("secondary", "outcomes_checking", parameters, record_id)
    return answer




def get_AI_data_results2(AI, study_id, record_id, project_id):
    # TODO modif en cours
    AI_data = dict()
    context_source = "abstract" if AI == 1 else "pdf"
    data = AI_results2(study_id, record_id, project_id, context_source)
    return data

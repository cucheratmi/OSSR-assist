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
    median_1: str = Field(description="median of the experimental group")
    median_0: str = Field(description="median of the control group")
    n_1: int = Field(description="sample size of the experimental group")
    n_0: int = Field(description="sample size of the control group")
    events_1: int = Field(description="number of events in the experimental group")
    events_0: int = Field(description="number of events in the control group")
    source: str = Field(description="text extracts used to obtain these values")
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




def get_AI_data_results2(AI, study_id, record_id, project_id, llm_name=None):
    if llm_name is None:
        llm_name=current_app.config['LLM_NAME']

    AI_data = dict()
    context_source = "abstract" if AI == 30 else "pdf"
    if llm_name == LLM_Name_Enum.ANTHROPIC.value and context_source == "pdf":
        data = get_AI_data_results_json(study_id, record_id, project_id, llm_name)
    elif llm_name == LLM_Name_Enum.MISTRAL.value and context_source == "pdf":
        data = get_AI_data_results_json(study_id, record_id, project_id, llm_name)
    else:
        data = AI_results2(study_id, record_id, project_id, context_source)

    return data



#### json #####

def get_AI_data_results_json(study_id: int, record_id: int, project_id: int, llm_name: str) -> any:

    json_hazard_ratio = (' "hazard ratio": "value", "confidence interval lower limit": "value", "confidence interval upper limit": "value", '
                         '"median experimental group": "value and confidence interval", "median control group": "value and confidence interval", '
                         ' "sample size experimental group": "value", "sample size control group": "value", "number of events experimental group": "value", "number of events control group": "value"  '
                         '"p value": "value", "results in one sentence": "value", '
                         '"source": "text extracts used to obtain these values", '
                         '"paper endpoint name": "endpoint name as used in the text" ')

    sql = "SELECT id, name, description FROM outcomes WHERE project=?"
    r = sql_select_fetchall(sql, (project_id,))
    outcomes_list = ""
    json1 = list()
    outcome_ids = dict()
    for o in r:
        outcome = o['name'] + " (" + o['description'] + "), id:" + str(o['id'])
        outcomes_list += " - " + outcome + "\n"
        outcome_ids[o['name']] = o['id']
        json1.append('{"outcome name": "' + o['name']+ '", "' + json_hazard_ratio + "}")

    json_template = '[' + ', '.join(json1) + ']'
    parameters = {'outcomes_list': outcomes_list, 'json_template': json_template}

    j = invoke_llm_PDF_json_output("results_json", parameters, record_id,llm_name)

    AI_data = dict()
    for e in j:
        outcome_name = e['outcome name']
        r = dict()
        r['outcome_name'] = outcome_name
        r['hazard_ratio'] = e['hazard ratio']
        r['ll'] = e['confidence interval lower limit']
        r['ul'] = e['confidence interval upper limit']
        r['median_1'] = e['median experimental group']
        r['median_0'] = e['median control group']
        r['n_1'] = e['sample size experimental group']
        r['n_0'] = e['sample size control group']
        r['events_1'] = e['number of events experimental group']
        r['events_0'] = e['number of events control group']
        r['p_value'] = e['p value']
        r['literal_summary'] = e['results in one sentence']
        r['source'] = e['source']
        r['paper_endpoint_name'] = e['paper endpoint name']

        AI_data[outcome_ids[outcome_name]] = r

    return AI_data
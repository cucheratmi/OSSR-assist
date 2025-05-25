import sqlite3
from os.path import exists

from flask import Flask, render_template, request, redirect, url_for, make_response, flash, session
from pandas.core.window.doc import template_see_also

import references
from pdfs import test_if_pdf_exists
from utils import *
from AI_extraction import *
from AI_ROB import *
from AI_outcomes import *
from outcomes import *
from experimental_script import *


def studies_list(project_id):
    sql = "SELECT id, name FROM studies WHERE project=? ORDER BY name"
    studies = sql_select_fetchall(sql, (project_id,))

    project_name, study_type, eligibility_criteria_empty = get_project_name(project_id)

    return render_template('studies_list.html', project_id=project_id, project_name=project_name,
                           studies=studies, eligibility_criteria_empty=eligibility_criteria_empty)

def get_study_data(study_id):
    sql = """
    SELECT studies.*,
        projects.name AS project_name
    FROM studies 
        INNER JOIN projects ON projects.id=studies.project
    WHERE studies.id=? 
    """
    parameters = (study_id,)
    study_data = sql_select_fetchone(sql, (study_id,))

    return study_data


def get_fields_data(study_id, project_id):
    sql = """
    SELECT study_fields.name AS field_name, study_fields.id AS field_id, study_field_values.value AS value, study_fields.description AS description
    FROM study_fields
        LEFT JOIN study_field_values ON study_field_values.field = study_fields.id
            AND study_field_values.study = ?
    WHERE study_fields.project = ?
    """
    data_fields = sql_select_fetchall(sql, (study_id,project_id,))
    for e in data_fields:
        label = e['field_name']
        label = label.replace("_", " ")
        e['label'] = label
    return data_fields

def study_edit(study_id, project_id):
    study_data = get_study_data(study_id)
    data_fields = get_fields_data(study_id, project_id)
    references = get_references(study_id) 

    return render_template('study_edit.html', study_id=study_id, study_data=study_data, project_id=project_id, references=references, data_fields=data_fields,)


def study_delete(study_id, project_id):
    sql = "UPDATE records SET selection=0 WHERE records.id IN (SELECT record FROM rel_study_records WHERE study=?)"
    sql_update(sql, (study_id,))

    sql= "DELETE FROM rel_study_records WHERE study=?"
    sql_delete(sql, (study_id,))

    sql = "DELETE FROM study_field_values WHERE study=?"
    sql_delete(sql, (study_id,))

    sql = "DELETE FROM studies WHERE id=?"
    sql_delete(sql, (study_id,))

    return redirect(url_for("endpoint_studies_list", project_id=project_id))

def study_delete2(study_id, project_id):
    sql = "UPDATE records SET selection=0 WHERE records.id IN (SELECT record FROM rel_study_records WHERE study=?)"
    sql_update(sql, (study_id,))

    sql= "DELETE FROM rel_study_records WHERE study=?"
    sql_delete(sql, (study_id,))

    sql = "DELETE FROM study_field_values WHERE study=?"
    sql_delete(sql, (study_id,))

    sql = "DELETE FROM studies WHERE id=?"
    sql_delete(sql, (study_id,))

    return make_response('', 200)




def study_add(project_id):
    sql = "INSERT INTO studies (name, project) VALUES (?,?)"
    study_id = sql_insert_into(sql, ("new study",project_id))
    return redirect(url_for("endpoint_study_edit", study_id=study_id, project_id=id))

def study_extraction_AI1(study_id, record_id):
    # TODO a efefcaer
    sql = "SELECT pmid FROM records WHERE id=?"
    pmid = sql_select_fetchone(sql, (record_id,))['pmid']
    return study_extraction_from_pubmed_abstract(study_id, pmid)


def study_panel1(study_id, project_id):
    study_data = get_study_data(study_id)
    return render_template("study_panel1.html", study_id=study_id, project_id=project_id, study_data=study_data)

def study_panel_references(study_id, project_id, record_id=0):
    references = get_references(study_id)
    pdf_exists = test_if_pdf_exists(record_id)

    data_fields = get_fields_data(study_id, project_id)

    return render_template("panel_references.html", study_id=study_id, project_id=project_id, references=references,
                           record_id=record_id, data_fields=data_fields, pdf_exists=pdf_exists)


def get_references_and_selected_reference(study_id, record_id):
    references = get_references(study_id)
    selected_reference = None
    pdf_exists = False
    if record_id is not None:
        selected_reference = next((ref for ref in references if ref['id'] == record_id), None)
        pdf_exists = test_if_pdf_exists(record_id)
    return references, selected_reference, pdf_exists


def get_ROB(study_id, project_id):

    #get the type of study for the corresponding ROB
    sql = "SELECT type_of_study FROM projects WHERE id=?"
    project_type = sql_select_fetchone(sql, (project_id,))['type_of_study']

    d = dict()
    ROB_DOMAIN = None
    match project_type:
        case TypeOfStudy.DIAG.value:
            ROB_DOMAIN = ROB_DIAG_DOMAIN
            LEVEL_NAME = {0:'', 1:'low risk', 2:'some concern', 3:'high risk'}
            for i in range(1, len(ROB_DOMAIN)+1):
                d[i] = {'domain': i, 'domain_name': ROB_DOMAIN[i], 'level': 0, 'level_name':'', 'justification': ''}
        case _:
            ROB_DOMAIN = ROB_RCT_DOMAIN
            LEVEL_NAME = {0:'', 1:'low risk of bias', 2:'some concern', 3:'high risk of bias'}
            for i in range(1, 6):
                d[i] = {'domain':i, 'domain_name': ROB_RCT_DOMAIN[i], 'level':0, 'level_name':'', 'justification': ''}

    sql = "SELECT domain, level, justification FROM ROB_values where study=?"
    rows = sql_select_fetchall(sql, (study_id,))
    for row in rows:
        i = int(row['domain'])
        d[i]['level'] = int(row['level'])
        d[i]['level_name'] = LEVEL_NAME[int(row['level'])]
        d[i]['justification'] = row['justification']

    return d, ROB_DOMAIN

def set_ROB_level(study, domain):
    level =  request.form['level_'+str(domain)]
    print(f"{study=} {domain=} {level=}")
    sql = "INSERT OR IGNORE INTO ROB_values (study, domain, level) VALUES (?,?,?);"
    sql_update(sql, (study, domain, level,))
    sql = "UPDATE ROB_values SET level=? WHERE study=? AND domain=?"
    sql_update(sql, (level, study, domain,))

    return '', 200

def set_ROB_justification(study, domain):
    justification =  request.form['justification_'+str(domain)]
    print(f"{study=} {domain=} {justification=}")
    sql = "INSERT OR IGNORE INTO ROB_values (study, domain, justification) VALUES (?,?,?);"
    sql_update(sql, (study, domain, justification,))
    sql = "UPDATE ROB_values SET justification=? WHERE study=? AND domain=?"
    sql_update(sql, (justification, study, domain,))

    return '', 200


def get_research_questions(study_id, project_id):
    sql = """
          SELECT research_questions.id, research_questions.name, rel_study_QRs.study 
          FROM research_questions
              LEFT JOIN rel_study_QRs ON rel_study_QRs.research_question = research_questions.id AND rel_study_QRs.study = ?
          WHERE research_questions.project = ?  
          """
    rows = sql_select_fetchall(sql, (study_id, project_id,))
    return rows


def study_fullscreen(study_id, project_id, record_id, tab, AI):
    llm_name = current_app.config['LLM_NAME']
    project_name, _, _ = get_project_name(project_id)
    references = get_references(study_id)
    if record_id == 0 and len(references) == 1:
        record_id = list(references.values())[0]['id']
    pdf_exists = test_if_pdf_exists(record_id)
    study_data = get_study_data(study_id)

    if tab=="chat":
        return tab_chat(study_id, project_id, record_id, tab, llm_name, project_name, references, pdf_exists,  study_data)
    else:
        return tabs(study_id, project_id, record_id, tab, AI, llm_name, project_name, references, pdf_exists,  study_data)


def tab_chat(study_id, project_id, record_id, tab, llm_name, project_name, references, pdf_exists,  study_data):
    question = request.form.get('question')
    answer = None
    if question !="" and question is not None:
        parameters = dict(question=question)
        answer = invoke_llm_PDF_text_output("primary", "chat_with_paper", parameters, record_id)
        import mistune
        answer = mistune.html(answer)

    exemple_questions = None
    with open('questions.json', 'r', encoding='utf-8') as file:
        exemple_questions = json.load(file)

    return render_template('study_fullscreen_chat.html',
                           study_id=study_id, project_id=project_id, project_name=project_name, pdf_exists=pdf_exists,
                           record_id=record_id, tab=tab,
                           references=references,  study_data=study_data,
                           question=question, answer=answer, exemple_questions=exemple_questions,
                           LLM_name=llm_name, primary_LLM_available=is_primary_LLM_available(),secondary_LLM_available=is_secondary_LLM_available())


def tabs(study_id, project_id, record_id, tab, AI, llm_name, project_name, references, pdf_exists, study_data):

    ROB = None
    ROB_DOMAIN = None
    results_data = None
    data_fields = None
    template= None
    research_questions = None
    if tab=="ROB":
        ROB, ROB_DOMAIN = get_ROB(study_id, project_id)
        template= 'study_fullscreen_ROB.html'
    elif tab=="fields":
        data_fields = get_fields_data(study_id, project_id)
        template= 'study_fullscreen_fields.html'
    elif tab=="outcomes2":
        results_data = get_results_data(study_id, project_id)
        template= 'study_fullscreen_outcomes2.html'
    elif tab=="experimental":
        template = "study_fullscreen_experimental.html"
    else:
        research_questions = get_research_questions(study_id, project_id)
        if len(research_questions) == 0:
            research_questions = None
        template= 'study_fullscreen_tab1.html'

    #### AI #####
    AI_data = dict()
    if AI==1 or AI==2: # extraction from abstract or pdf
        AI_data = get_AI_data_extraction(AI, study_id, record_id, project_id)
    if AI == 10:  #rob
        AI_data = get_AI_data_ROB(study_id, record_id, project_id)
    if AI==30 or AI==31: # outcomes2
        AI_data = get_AI_data_results2(AI, study_id, record_id, project_id)
    # if AI==41:
    #     # outcome pdf ocr json source
    #     AI_data = get_AI_data_results_json(study_id, record_id, project_id)


    return render_template(template,
                           study_id=study_id,project_id=project_id, project_name=project_name, pdf_exists=pdf_exists, record_id=record_id, tab=tab,
                           references=references, study_data=study_data, research_questions=research_questions,
                           data_fields=data_fields,
                           ROB=ROB, ROB_DOMAIN=ROB_DOMAIN,
                           results_data=results_data, OUTCOMES_TYPES=OUTCOMES_TYPES,
                           AI_data=AI_data, AI=AI,
                           LLM_name=llm_name, primary_LLM_available=is_primary_LLM_available(), secondary_LLM_available=is_secondary_LLM_available() )



def study_llamaindex_extract(study_id, project_id, record_id):
    if os.environ.get('LLAMA_CLOUD_API_KEY') is None:
        return "LLAMA_CLOUD_API_KEY not set", 400

    project_name, _, _ = get_project_name(project_id)
    references = get_references(study_id)
    if record_id == 0 and len(references) == 1:
        record_id = list(references.values())[0]['id']

    pdf_exists = test_if_pdf_exists(record_id)
    llm_name = current_app.config['LLM_NAME']

    extracted_data = llamaindexextract_field_extraction(study_id, record_id, project_id)

    return render_template('study_fullscreen_experimental.html',
                           study_id=study_id,project_id=project_id, project_name=project_name, pdf_exists=pdf_exists, record_id=record_id, tab="experimental",
                           extracted_data=extracted_data,
                           study_data = get_study_data(study_id), references = references,
                           ROB = None, ROB_DOMAIN = None, results_data = None, data_fields = None, research_questions = None,
                           LLM_name=llm_name, primary_LLM_available=is_primary_LLM_available(),secondary_LLM_available=is_secondary_LLM_available(),
                           )


def study_llamaindex_extract_outcomes(study_id, project_id, record_id):
    extracted_data = llamaindexextract_outcomes_extraction(study_id, record_id, project_id)
    return render_template('experimental_outcomes.html',)

def study_compare_extraction(study_id, project_id, record_id):
    AI = 2 # pdf
    models = (LLM_Name_Enum.LLAMAINDEX_EXTRACT.value, LLM_Name_Enum.OPENAI.value, LLM_Name_Enum.ANTHROPIC.value, LLM_Name_Enum.MISTRAL.value)

    AI_data = dict()
    for llm_name in models:
        if llm_name == LLM_Name_Enum.LLAMAINDEX_EXTRACT.value:
            llamaindexextract_field_extraction(study_id, record_id, project_id)
        else:
            r = get_AI_data_extraction(AI, study_id, record_id, project_id, llm_name)

        for i in range(1, len(r)-1):
            field_name = r[i]['field_name'].strip()
            e = dict(value=r[i]['extracted_value'], source=r[i]['source'])

            if field_name not in AI_data:
                AI_data[field_name] = [e,]
            else:
                AI_data[field_name].append(e)

    return render_template('llm_comparison_extraction.html',
                           study_id=study_id, project_id=project_id, record_id=record_id,
                           AI_data=AI_data, models=models,)


def study_compare_outcome(study_id, project_id, record_id):
    models = (LLM_Name_Enum.OPENAI.value, LLM_Name_Enum.ANTHROPIC.value, LLM_Name_Enum.MISTRAL.value)

    results_data = dict()
    for llm_name in models:
        r = get_AI_data_results2(2, study_id, record_id, project_id, llm_name)
        for k,v in r.items():
            outcome_name = v['outcome_name']
            s = f"HR={v['hazard_ratio']} 95% CI [{v['ll']};{v['ul']}], p={v['p_value']}"
            s+= f"<br/>{v['median_1']} {v['median_0']}"
            s+= f"<br/>{v['events_1']}/{v['n_1']} {v['events_0']}/{v['n_0']}"
            s+= f"<br/>source: {v['source']}"
            s+= f"<br/>{v['literal_summary']}"
            s+= f"<br/>{v['paper_endpoint_name']}"

            if outcome_name not in results_data:
                results_data[outcome_name] = []
            results_data[outcome_name].append(s)

    return render_template('llm_comparison_outcomes.html',
                           study_id=study_id, project_id=project_id, record_id=record_id,
                           results_data=results_data)


def study_check_extraction(study_id, project_id, record_id):
    data = get_fields_data(study_id, project_id)
    extracted_data = ""
    for e in data:
        extracted_data += f" - {e['field_name']}: {e['value']}\n"

    answer = AI_check_extraction(extracted_data, record_id)

    if True:
        # model answer is considered as being markdown that will be convert to HTML
        import mistune
        html = mistune.html(answer)
    else:
        html = "<pre class='p-2 text-monospace' style='white-space: pre-wrap;'>" + \
        answer + \
        "</pre>"

    html = "<div class='alert alert-light'>"+\
           "<h4 class='alert-heading'>✨ AI check </h4>" + \
            html +\
            "</div>"

    return html

def study_check_ROB(study_id, project_id, record_id):
    data, ROB_DOMAIN = get_ROB(study_id, project_id)
    extracted_data = ""
    for i in ROB_DOMAIN.keys():
        #{'domain':i, 'domain_name':ROB_DOMAIN[i], 'level':0, 'justification':''}
        level_name = data[i]['level_name']
        extracted_data += f" - {data[i]['domain_name']}: {level_name}\n"

    answer = AI_check_ROB(extracted_data, record_id, project_id)

    if True:
        # model answer is considered as being markdown that will be convert to HTML
        import mistune
        html = mistune.html(answer)
    else:
        html = "<pre class='p-2 text-monospace' style='white-space: pre-wrap;'>" + \
        answer + \
        "</pre>"

    html = "<div class='alert alert-light'>"+\
           "<h4 class='alert-heading'>✨ AI check </h4>" + \
            html +\
            "</div>"

    return html


def get_outcomes_data(study_id):
    sql = """
    SELECT outcome_values.*, outcomes.name AS outcome_name 
    FROM outcome_values 
        INNER  JOIN outcomes ON outcomes.id=outcome_values.outcome 
    WHERE outcome_values.study=? 
    """
    outcomes = sql_select_fetchall(sql, (study_id,))
    return outcomes

def study_check_outcomes(study_id, record_id):
    outcomes = get_outcomes_data(study_id)
    extracted_data = ""
    for o in outcomes:
        extracted_data += f" - {o['outcome_name']}: treatment effect: {o['TE']}, confidence interval; [{o['ll']};{o['ul']}], p value: {o["p_value"]}   \n"

    answer = AI_check_outcomes(extracted_data, record_id)

    if True:
        # model answer is considered as being markdown that will be convert to HTML
        import mistune
        html = mistune.html(answer)
    else:
        html = "<pre class='p-2 text-monospace' style='white-space: pre-wrap;'>" + \
        answer + \
        "</pre>"

    html = "<div class='alert alert-light'>"+\
           "<h4 class='alert-heading'>✨ AI check </h4>" + \
            html +\
            "</div>"

    return html






def study_run_experimental_script(script, study_id, project_id, record_id):
    from io import StringIO
    import sys

    buffer = StringIO()

    old_stdout = sys.stdout
    sys.stdout = buffer

    match script:
        case 1:
            experimental_script_1(study_id, record_id, project_id)
        case _:
            pass

    sys.stdout = old_stdout

    return buffer.getvalue()


def study_llamaindex_parse(study_id, project_id, record_id):
    from llama_parse import LlamaParse

    parser = LlamaParse(
        result_type="markdown",  # "markdown" and "text" are available
    )

    file_name = f"r{record_id}.pdf"
    pdf_path = os.path.join(PDF_UPLOAD_PATH, file_name)
    extra_info = {"file_name": file_name}

    documents =""
    with open(pdf_path, "rb") as f:
        documents = parser.load_data(f, extra_info=extra_info)

        with open('./tempo/output.md', 'w', encoding='utf-8') as f2:
            for doc in documents:
                print(doc.text, file=f2)

    return ""



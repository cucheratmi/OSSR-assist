import sqlite3
from os.path import exists

from flask import Flask, render_template, request, redirect, url_for, make_response, flash, session
from pandas.core.window.doc import template_see_also

import references
from pdfs import test_if_pdf_exists
from utils import *
from AI_extraction import *
from AI_ROB import *
from outcomes import *

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
            LEVEL_NAME = {0:'', 1:'low risk', 2:'some concern', 3:'high risk'}
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


# def study_fullscreen_old(study_id, project_id, record_id=0, tab="study"):
#     study_data = get_study_data(study_id)
#     data_fields = get_data_fields(study_id, project_id)
#     references = get_references(study_id)
#     pdf_exists = test_if_pdf_exists(record_id)
#     ROB = get_ROB(study_id)
#
#     if False: # AI
#         extracted_data = study_extraction_personalised_fields(study_id, record_id, project_id, "abstract")
#     else:
#         extracted_data = dict()
#
#     return render_template('study_fullscreen_old.html', study_id=study_id, references=references, study_data=study_data,
#                            project_id=project_id, data_fields=data_fields,pdf_exists=pdf_exists, record_id=record_id, tab=tab, ROB=ROB,
#                            extracted_data=extra)


def study_fullscreen(study_id, project_id, record_id, tab, AI):
    project_name, _, _ = get_project_name(project_id)

    study_data = get_study_data(study_id)
    references = get_references(study_id)
    if record_id == 0 and len(references) == 1:
        record_id = list(references.values())[0]['id']

    pdf_exists = test_if_pdf_exists(record_id)

    ROB = None
    ROB_DOMAIN = None
    results_data = None
    data_fields = None
    template= None
    if tab=="ROB":
        ROB, ROB_DOMAIN = get_ROB(study_id, project_id)
        template= 'study_fullscreen_ROB.html'
    elif tab=="fields":
        data_fields = get_fields_data(study_id, project_id)
        template= 'study_fullscreen_fields.html'
    elif tab=="outcomes2":
        results_data = get_results_data(study_id, project_id)
        template= 'study_fullscreen_outcomes2.html'
    else:
        template= 'study_fullscreen_tab1.html'

    #### AI #####
    AI_data = dict()
    if AI==1 or AI==2: # extraction from abstract or pdf
        AI_data = get_AI_data_extraction(AI, study_id, record_id, project_id)
    if AI == 10:  #rob
        AI_data = get_AI_data_ROB(study_id, record_id, project_id)
    if AI==30 or AI==31: # outcomes2
        AI_data = get_AI_data_results2(AI, study_id, record_id, project_id)


    return render_template(template, study_id=study_id,
                           project_id=project_id, project_name=project_name, pdf_exists=pdf_exists, record_id=record_id, tab=tab,
                           references=references, study_data=study_data,
                           data_fields=data_fields,
                           ROB=ROB, ROB_DOMAIN=ROB_DOMAIN,
                           results_data=results_data,
                           AI_data=AI_data, AI=AI,
                           primary_LLM_available=is_primary_LLM_available(), secondary_LLM_available=is_secondary_LLM_available() )


def get_AI_data_extraction(AI, study_id, record_id, project_id):
    AI_data = dict()
    context_source = "abstract" if AI == 1 else "pdf"
    data = AI_extraction_personalised_fields(study_id, record_id, project_id, context_source)
    for e in data:
        i = int(e[0][1:])
        AI_data[i] = e[1]
    return AI_data

# def get_AI_data_results(AI, study_id, record_id, project_id):
#     AI_data = dict()
#     context_source = "abstract" if AI == 1 else "pdf"
#     data = AI_results(study_id, record_id, project_id, context_source)
#     for e in data:
#         i = int(e[0][1:])
#         AI_data[i] = e[1]
#     return AI_data

def get_AI_data_results2(AI, study_id, record_id, project_id):
    # TODO modif en cours
    AI_data = dict()
    context_source = "abstract" if AI == 1 else "pdf"
    data = AI_results2(study_id, record_id, project_id, context_source)
    return data

def get_AI_data_ROB(study_id, record_id, project_id):
    AI_data = AI_ROB(study_id, record_id, project_id, current_app.config['LLM_NAME'])
    return AI_data


# def study_fullscreen_AI(study_id, project_id, record_id=0):
#     # TODO deprecated
#     references = get_references(study_id)
#     pdf_exists = test_if_pdf_exists(record_id)
#
#     extracted_data = []
#     return render_template('study_fullscreen_AI.html', study_id=study_id, project_id=project_id,
#                            references=references, pdf_exists=pdf_exists, record_id=record_id, extracted_data=extracted_data )


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





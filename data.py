import math
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, make_response, send_file

from utils import *
import pandas as pd
import io


def get_data(project_id):
    sql="SELECT name FROM study_fields WHERE project=? ORDER BY sort_order, id"
    fields_ordered = sql_select_fetchall(sql, (project_id,))
    fields_ordered = list(map(lambda x: x['name'], fields_ordered))
    print(fields_ordered)

    sql="""
    SELECT studies.name AS study_name, study_fields.name AS field_name, study_field_values.value AS value 
    FROM studies
        INNER JOIN study_field_values ON study_field_values.study = studies.id 
        INNER JOIN study_fields ON study_fields.id = study_field_values.field 
    WHERE studies.project=? AND study_fields.project=?
    ORDER BY study_fields.sort_order, studies.name
    """
    data = sql_select_fetchall(sql, (project_id, project_id, ))
    if data is None: return None
    if len(data) == 0: return None

    df = pd.DataFrame(data)
    df2 = df.pivot(index='study_name', columns='field_name', values='value')

    df2.columns = [col for col in df2.columns]
    df2.reset_index(inplace=True)

    df2 = df2.reindex(columns=['study_name'] + fields_ordered)

    return df2

def data_list1(project_id):

    project_name, study_type, eligibility_criteria_empty = get_project_name(project_id)

    df2 = get_data(project_id)
    if df2 is None: return render_template('data1.html', project_id=project_id, project_name=project_name,
                                           eligibility_criteria_empty=eligibility_criteria_empty,
                                           html="No data available")

    # styler = df2.style
    # styler.set_table_attributes('class="table table-condensed table-hover table-sm" id="data"')
    # html = styler.to_html(table_id="data",)

    html = df2.to_html(index=False, table_id="data", classes="table table-striped table-hover table-sm table_small")

    return render_template('data1.html', project_id=project_id, project_name=project_name,
                           eligibility_criteria_empty=eligibility_criteria_empty, html=html)


def data_csv1(project_id):
    df2 = get_data(project_id)
    if df2 is None: return "no data available."

    response = make_response(df2.to_csv())
    response.headers['Content-Disposition'] = 'attachment; filename=data.csv'
    response.headers['Content-type'] = 'text/csv'

    return response


def data_excel1(project_id):
    df2 = get_data(project_id)
    if df2 is None: return "no data available."

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        df2.to_excel(writer)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', download_name='data.xlsx')


def get_rob_domain(study_type):
    match study_type:
        case TypeOfStudy.DIAG.value:
            ROB_DOMAIN = ROB_DIAG_DOMAIN
            ROB_LEVEL_NAME = {0:'', 1:'low risk', 2:'some concern', 3:'high risk'}
        case _:
            ROB_DOMAIN = ROB_RCT_DOMAIN
            ROB_LEVEL_NAME = {0:'', 1:'low risk', 2:'some concern', 3:'high risk'}
    return ROB_DOMAIN, ROB_LEVEL_NAME

def get_ROB_data(project_id, study_type):
    ROB_DOMAIN, ROB_LEVEL_NAME = get_rob_domain(study_type)

    sql = """ \
          SELECT studies.name             AS study_name, \
                 ROB_values.domain        AS domain, \
                 ROB_values.level         AS level, \
                 ROB_values.justification AS justification \
          FROM studies \
                   INNER JOIN ROB_values ON ROB_values.study = studies.id \
          WHERE studies.project = ? \
          ORDER BY studies.name, rob_values.domain \
         """
    rows = sql_select_fetchall(sql, (project_id,))

    current_study = None
    studies = list()
    study = dict()
    rob = dict()
    for r in rows:
        study_name = r['study_name']

        if study_name != current_study:
            if current_study is not None:
                study['rob'] = rob
                studies.append(study)

            current_study = study_name
            study = {'study_name': study_name}
            rob = dict()
            for i in ROB_DOMAIN.keys():
                rob[i] = {'domain': ROB_DOMAIN[i], 'level': None, 'level_name':'', 'justification': None}

        domain = r['domain']
        level = r['level']
        level_name = ROB_LEVEL_NAME[level]
        justification = r['justification']

        rob[domain]['level'] = level
        rob[domain]['level_name'] = level_name
        rob[domain]['justification'] = justification
        rob[domain]['risk_of_bias'] = level_name

    study['rob'] = rob
    if 'study_name' in study.keys():
        studies.append(study)

    return studies, ROB_DOMAIN

def get_outcomes_data_short_format(project_id):
    sql = "SELECT name FROM projects WHERE id=?"
    r = sql_select_fetchone(sql, (project_id,))
    project_name = r['name']
    file_name = "project_" + str(project_id) + "_" + project_name.strip().replace(" ","_") + "_data"

    rows = outcomes_short_format(project_id)
    df = pd.DataFrame(rows)
    df.columns = ["research_question_id","research_question_name","study_name", "outcome_name", "TE", "ll","ul","n_1","n_0","events_1","events_0","p_value","comment"]

    response = make_response(df.to_csv())
    response.headers['Content-Disposition'] = 'attachment; filename=' + file_name+ '.csv'
    response.headers['Content-type'] = 'text/csv'

    return response

def outcomes_short_format(project_id):
    sql = """ \
          SELECT 
                research_questions.id AS research_question_id, research_questions.name AS research_question, 
                studies.name AS study_name, 
                outcomes.name AS outcome_name, 
                outcome_values.TE, outcome_values.ll, outcome_values.ul, outcome_values.n_1, outcome_values.n_0, outcome_values.events_1, outcome_values.events_0,
                outcome_values.p_value, outcome_values.paper_designation
          FROM studies 
                INNER JOIN outcome_values ON outcome_values.study = studies.id 
                INNER JOIN outcomes ON outcomes.id = outcome_values.outcome 
                LEFT JOIN rel_study_QRs ON rel_study_QRs.study = studies.id
                LEFT JOIN research_questions ON research_questions.id = rel_study_QRs.research_question
          WHERE studies.project = ? 
          ORDER BY research_questions.id, studies.name, outcome_values.outcome 
         """
    rows = sql_select_fetchall(sql, (project_id,))
    return rows


def get_results_data(project_id):
    sql = "SELECT id, name FROM outcomes WHERE project=? ORDER BY sort_order, id"
    r = sql_select_fetchall(sql, (project_id,))
    outcomes_list = {outcome['id']: outcome['name'] for outcome in r}

    sql = """ 
          SELECT outcome_values.outcome AS outcome_id, 
                 outcome_values.*, 
                 studies.name AS study_name 
          FROM studies 
                   INNER JOIN outcome_values ON outcome_values.study = studies.id 
          WHERE studies.project = ? 
          ORDER BY studies.name, outcome_values.outcome 
         """
    rows = sql_select_fetchall(sql, (project_id,))

    current_study = None
    studies = list()
    study = dict()
    results = dict()
    for r in rows:
        study_name = r['study_name']

        if study_name != current_study:
            if current_study is not None:
                study['results'] = results
                studies.append(study)

            current_study = study_name
            study = {'study_name': study_name}
            results = dict()
            for i in outcomes_list.keys():
                results[i] = ""

        results[int(r['outcome_id'])] = r['value']

    study['results'] = results
    studies.append(study)

    return studies, outcomes_list

def table_results(project_id):
    project_name, study_type, eligibility_criteria_empty = get_project_name(project_id)

    studies, outcomes_list = get_results_data(project_id)
    lg = math.ceil(85 / len(outcomes_list)) if len(outcomes_list)>0 else 50

    short_format = outcomes_short_format(project_id)

    return render_template('table_results.html', studies=studies,
                           outcomes_list=outcomes_list, lg=lg, short_format = short_format,
                           eligibility_criteria_empty=eligibility_criteria_empty,
                           project_id=project_id, project_name=project_name)

def table_results_as_dataframe(project_id):
    data, outcomes_list = get_results_data(project_id)

    columns_name = ['study_name']
    for i in outcomes_list.keys():
        columns_name.append(outcomes_list[i].replace(" ", "_"))

    df = pd.DataFrame(columns=columns_name)

    for study in data:
        row = [study['study_name'],]
        results = study['results']
        for i in outcomes_list.keys():
            row.append(results[i])
        df.loc[len(df)] = row

    return df

def data_results_for_export(project_id):
    sql = "SELECT name FROM projects WHERE id=?"
    r = sql_select_fetchone(sql, (project_id,))
    project_name = r['name']
    file_name = "project_" + str(project_id) + "_" + project_name.strip().replace(" ","_") + "_results"

    df = table_results_as_dataframe(project_id)
    return df, file_name

def data_results_csv(project_id):
    df, file_name = data_results_for_export(project_id)
    if df is None: return "no data available."

    response = make_response(df.to_csv())
    response.headers['Content-Disposition'] = 'attachment; filename=' + file_name+ '.csv'
    response.headers['Content-type'] = 'text/csv'

    return response

def data_results_excel(project_id):
    df, file_name = data_results_for_export(project_id)
    if df is None: return "no data available."

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name= file_name + '.xlsx')







def table_ROB(project_id):
    project_name, study_type, eligibility_criteria_empty = get_project_name(project_id)

    studies, ROB_DOMAIN = get_ROB_data(project_id, study_type)
    lg = math.ceil(85 / len(ROB_DOMAIN)) if len(ROB_DOMAIN)>0 else 50
    return render_template('table_ROB.html', studies=studies, ROB_DOMAIN=ROB_DOMAIN, lg=lg,
                           eligibility_criteria_empty=eligibility_criteria_empty,
                           project_id=project_id, project_name=project_name)


def table_ROB_as_dataframe(project_id, study_type):
    data, ROB_DOMAIN = get_ROB_data(project_id, study_type)

    columns_name = ['study_name']
    for i in ROB_DOMAIN.keys():
        columns_name.append(ROB_DOMAIN[i].replace(" ", "_") + "_risk_of_bias")
        columns_name.append(ROB_DOMAIN[i].replace(" ", "_") + "_justification")

    df = pd.DataFrame(columns=columns_name)

    for study in data:
        row = [study['study_name'],]
        rob = study['rob']
        for i in ROB_DOMAIN.keys():
            row += [rob[i]['risk_of_bias'], rob[i]['justification']]
        df.loc[len(df)] = row

    return df


def data_ROB_for_export(project_id):
    sql = "SELECT name, type_of_study FROM projects WHERE id=?"
    r = sql_select_fetchone(sql, (project_id,))
    study_type  = r['type_of_study']
    project_name = r['name']
    file_name = "project_" + str(project_id) + "_" + project_name.strip().replace(" ","_") + "_rob"

    df = table_ROB_as_dataframe(project_id, study_type)
    return df, file_name

def data_ROB_csv1_project(project_id):
    df, file_name = data_ROB_for_export(project_id)
    if df is None: return "no data available."

    response = make_response(df.to_csv())
    response.headers['Content-Disposition'] = 'attachment; filename=' + file_name+ '.csv'
    response.headers['Content-type'] = 'text/csv'

    return response

def data_ROB_excel1(project_id):
    df, file_name = data_ROB_for_export(project_id)
    if df is None: return "no data available."

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer) as writer:
        df.to_excel(writer)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                     download_name= file_name + '.xlsx')



from flask import render_template, redirect, url_for, request, jsonify
from utils import *


def outcomes_setup(project_id):
    project_name,_, eligibility_criteria_empty = get_project_name(project_id)

    sql = "SELECT * FROM outcomes WHERE project=? ORDER BY sort_order, name"
    outcomes = sql_select_fetchall(sql, (project_id,))

    extraction_fields_list_empty = is_extraction_fields_list_empty(project_id)

    return render_template('project_setup_outcomes.html', project_id=project_id,
                           extraction_fields_list_empty=extraction_fields_list_empty,
                           project_name=project_name, eligibility_criteria_empty=eligibility_criteria_empty,
                           outcomes=outcomes, OUTCOMES_TYPES=OUTCOMES_TYPES)


def outcomes_add(project_id):
    name = request.form['name']
    name =name.strip().replace(" ","_")
    description = request.form['description']
    type = request.form['type']
    sql = "INSERT INTO outcomes (name, description, type, project) VALUES (?,?,?,?)"
    sql_insert_into(sql, (name, description, type, project_id))

    return redirect(url_for("endpoint_outcomes_setup", project_id=project_id))


def del_outcomes(outcome_id):
    sql = "DELETE FROM outcomes WHERE id=?"
    sql_delete(sql, (outcome_id,))
    return "", 200

def outcome_field_update(outcome_id, field_name):
    value = request.form[field_name]
    if field_name == "name":
        value = value.replace(" ","_")
    r = update_field("outcomes", outcome_id, field_name, value)
    return r, 200

def outcome_edit(outcome_id, project_id):
    sql = "SELECT * FROM outcomes WHERE id=?"
    outcome = sql_select_fetchone(sql, (outcome_id,))
    return render_template('outcome_edit.html', outcome_id=outcome_id, outcome=outcome, project_id=project_id, OUTCOMES_TYPES=OUTCOMES_TYPES)


def outcomes_order(project_id):
    new_order = request.get_json()
    print(new_order)
    i=1
    for outcome_id in new_order:
        sql = "UPDATE outcomes SET sort_order=? WHERE id=? AND project=?"
        parameters = (i, outcome_id, project_id)
        sql_update(sql, parameters)
        i+=1

def get_results_data(study_id, project_id):
    sql = """
          SELECT outcomes.name        AS outcome_name, \
                 outcomes.id          AS outcome_id, \
                 outcome_values.*, \
                 outcomes.description AS description
          FROM outcomes
                   LEFT JOIN outcome_values ON outcome_values.outcome = outcomes.id
              AND outcome_values.study = ?
          WHERE outcomes.project = ? \
          """
    results_data = sql_select_fetchall(sql, (study_id, project_id,))
    for e in results_data:
        label = e['outcome_name']
        label = label.replace("_", " ")
        e['label'] = label

        for k,v in e.items():
            if v is None:
                e[k] = ""

    return results_data


# def result_update(outcome_id, study_id):
#     # TODO potentially remove this
#     value = request.form["F"+str(outcome_id)]
#     try:
#         sql = "INSERT INTO outcome_values (outcome, study, value) VALUES (?,?,?)"
#         sql_insert_into(sql, (outcome_id, study_id, value))
#     except Exception as e:
#         print(e)
#
#     sql="UPDATE outcome_values SET value=? WHERE outcome=? AND study=?"
#     sql_update(sql, (value, outcome_id, study_id))
#
#     r = f"Outcome {outcome_id} updated for study {study_id} with value {value}"
#     return r, 200


def is_real(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

def result_update2(field_DB_name, outcome_id, study_id):
    field_HTML_name = field_DB_name + "_" + str(outcome_id)
    value = request.form[field_HTML_name].strip()

    valid = True
    if field_DB_name in ["TE","ll","ul"] and value!="":
        valid = is_real(value)
    elif field_DB_name in ["events_1","events_0","n_1","n_0"] and value!="":
        valid = value.isdigit()

    if valid:
        sql = "SELECT outcome, study FROM outcome_values WHERE outcome=? AND study=?"
        r = sql_select_fetchone(sql, (outcome_id, study_id,))
        if r is not None:
            sql=f"UPDATE outcome_values SET {field_DB_name}=? WHERE outcome=? AND study=?"
            sql_update(sql, (value, outcome_id, study_id))
        else:
            sql = f"INSERT INTO outcome_values (outcome, study, {field_DB_name}) VALUES (?,?,?)"
            sql_insert_into(sql, (outcome_id, study_id, value))

    c = "is-valid" if valid else "is-invalid"
    return jsonify({"className": "form-control " + c})



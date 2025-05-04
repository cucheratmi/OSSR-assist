from flask import render_template, redirect, url_for, request
from utils import *

def outcomes_setup(project_id):
    sql = "SELECT * FROM outcomes WHERE project=? ORDER BY sort_order, name"
    outcomes = sql_select_fetchall(sql, (project_id,))
    return render_template('project_setup_outcomes.html', project_id=project_id, outcomes=outcomes, OUTCOMES_TYPES=OUTCOMES_TYPES)


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
    return render_template('outcome_edit.html', outcome_id=outcome_id, outcome=outcome, project_id=project_id)


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
                 outcome_values.value AS value, \
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
        label = label[0].upper() + label[1:]
        e['label'] = label
    return results_data


def result_update(outcome_id, study_id):
    value = request.form["F"+str(outcome_id)]
    try:
        sql = "INSERT INTO outcome_values (outcome, study, value) VALUES (?,?,?)"
        sql_insert_into(sql, (outcome_id, study_id, value))
    except Exception as e:
        print(e)

    sql="UPDATE outcome_values SET value=? WHERE outcome=? AND study=?"
    sql_update(sql, (value, outcome_id, study_id))

    r = f"Outcome {outcome_id} updated for study {study_id} with value {value}"
    return r, 200
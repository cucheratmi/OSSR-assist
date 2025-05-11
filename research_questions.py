from flask import render_template, request, redirect, url_for

from utils import *


def research_questions_list(project_id):
    sql="SELECT * FROM research_questions WHERE project = ?"
    questions = sql_select_fetchall(sql, (project_id,))
    return render_template('research_questions_list.html', questions=questions, project_id=project_id)
 

def research_question_add(project_id):
    name = request.form['name'].strip()
    sql = "INSERT INTO research_questions (name, project) VALUES (?,?)"
    sql_insert_into(sql, (name, project_id))

    return redirect(url_for("endpoint_research_questions_list", project_id=project_id))


def del_research_question(research_question_id):
    sql = "DELETE FROM research_questions WHERE id=?"
    sql_delete(sql, (research_question_id,))

    sql = "DELETE FROM rel_study_QRs WHERE research_question=?"
    sql_delete(sql, (research_question_id,))

    return "", 200

def research_question_field_update(research_question_id, field_name):
    value = request.form[field_name]
    r = update_field("research_questions", research_question_id, field_name, value)
    return r, 200

def research_question_edit(research_question_id, project_id):
    sql = "SELECT * FROM research_questions WHERE id=?"
    research_question = sql_select_fetchone(sql, (research_question_id,))
    return render_template('research_question_edit.html', research_question_id=research_question_id, research_question=research_question, project_id=project_id)


def research_questions_order(project_id):
    new_order = request.get_json()
    print(new_order)
    i=1
    for research_questions_id in new_order:
        sql = "UPDATE research_questions SET sort_order=? WHERE id=?"
        parameters = (i, research_questions_id)
        sql_update(sql, parameters)
        i+=1

def set_study_research_question(study_id):
    print("fired")
    selected_values = request.form.getlist('research_question[]')
    print(selected_values)
    sql = "DELETE FROM rel_study_QRs WHERE study=?"
    sql_delete(sql, (study_id,))
    for research_question_id in selected_values:
        sql = "INSERT INTO rel_study_QRs (study, research_question) VALUES (?,?)"
        sql_insert_into(sql, (study_id, research_question_id))

    return "done"
    
from flask import Flask,render_template, jsonify, send_file, make_response, request, redirect, url_for

import time

import json

from utils import *

def projects_list():
    sql = "SELECT id, name FROM projects ORDER BY name"
    projects = sql_select_fetchall(sql, ())
    return render_template('projects_list.html', projects=projects)

def home():
    return projects_list()

def project_edit(id):
    sql = "SELECT * FROM projects WHERE id=?"
    project_data = sql_select_fetchone(sql, (id,))
    project_name = project_data['name']

    return render_template('project_setup_1.html', project_id=id, project_data=project_data, TypeOfStudy=TypeOfStudy, project_name=project_name)


def project_delete(project_id):
    # sql = "UPDATE projects SET deleted=1 WHERE id=?"
    # parameters = (project_id,)
    # sql_update(sql, parameters)

    sql = "DELETE FROM rel_study_records WHERE study IN (SELECT id FROM studies WHERE project=?)"
    parameters = (project_id,)
    sql_delete(sql, parameters)

    sql = "DELETE FROM study_field_values WHERE study IN (SELECT id FROM studies WHERE project=?)"
    parameters = (project_id,)
    sql_delete(sql, parameters)

    sql = "DELETE FROM studies WHERE project=?"
    parameters = (project_id,)
    sql_delete(sql, parameters)

    sql = "DELETE FROM records WHERE project=?"
    parameters = (project_id,)
    sql_delete(sql, parameters)

    sql = "DELETE FROM study_fields WHERE project=?"
    parameters = (project_id,)
    sql_delete(sql, parameters)

    sql = "DELETE FROM projects WHERE id=?"
    parameters = (project_id,)
    sql_delete(sql, parameters)

    return make_response('', 200)



def project_add():
    sql = "INSERT INTO projects (name) VALUES (?)"
    id = sql_insert_into(sql, ("new systematic review",))
    return project_edit(id)


def project_fields_edit(project_id):
    sql="SELECT name FROM projects WHERE id=?"
    project_name = sql_select_fetchone(sql, (project_id,))['name']

    sql = "SELECT * FROM study_fields where project=? ORDER BY sort_order"
    fields = sql_select_fetchall(sql, (project_id,))
    return render_template('project_setup_2.html', project_id=project_id, fields=fields, project_name=project_name)

def project_fields_update_order(project_id):
    new_order = request.get_json()
    print(new_order)
    i=1
    for field_id in new_order:
        sql = "UPDATE study_fields SET sort_order=? WHERE id=? AND project=?"
        parameters = (i, field_id, project_id)
        sql_update(sql, parameters)
        i+=1








def project_save(project_id):

    def get_dictionary_rows(sql, parameters):
        res = cur.execute(sql, parameters)
        columns = [description[0] for description in cur.description]
        rows = res.fetchall()

        # Convertir les données en liste de dictionnaires
        table_data = []
        for row in rows:
            row_dict = dict(zip(columns, row))
            table_data.append(row_dict)

        return table_data


    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    sql = "SELECT * FROM projects WHERE id=?"
    cur.execute(sql, (1,))
    columns = [description[0] for description in cur.description]
    row = cur.fetchone()
    project_dict = dict(zip(columns, row))
    project_name = project_dict['name']

    sql = """ \
          SELECT * \
          FROM study_fields \
          WHERE project = ? \
        """
    d = get_dictionary_rows(sql, (project_id,))
    project_dict['fields'] = d

    # studies
    sql = "SELECT * FROM STUDIES WHERE project=?"
    cur.execute(sql, (project_id,))
    studies = cur.fetchall()

    columns_studies = [description[0] for description in cur.description]
    studies_dict = []
    for study in studies:
        study_id = study['id']
        study_dict = dict(zip(columns_studies, study))

        sql = """
              SELECT *
              FROM records
                       INNER JOIN rel_study_records ON rel_study_records.record = records.id
              WHERE rel_study_records.study = ?
              """
        d = get_dictionary_rows(sql, (study_id,))
        for e in d:
            if isinstance(e['AI_answer'], bytes):
                e['AI_answer'] = e['AI_answer'].decode('utf-8')
        study_dict['records'] = d

        sql = """
              SELECT study_field_values.field, study_field_values.value, study_fields.name, study_fields.category
              FROM study_field_values
                       INNER JOIN study_fields ON study_fields.id = study_field_values.field
                       INNER JOIN studies ON studies.id = study_field_values.study
              WHERE study_field_values.study = ? \
              """
        d = get_dictionary_rows(sql, (study_id,))
        study_dict['fields'] = d

        studies_dict.append(study_dict)
        # print(studies_dict)
        project_dict['studies'] = studies_dict

    # records without study
    sql = """
          SELECT records.*
          FROM records
                   LEFT JOIN rel_study_records ON rel_study_records.record = records.id
          WHERE records.project = ? \
            AND rel_study_records.study IS NULL
          """
    d = get_dictionary_rows(sql, (project_id,))
    for e in d:
        if isinstance(e['AI_answer'], bytes):
            e['AI_answer'] = e['AI_answer'].decode('utf-8')

    project_dict['unselected_records'] = d

    ### save json file
    # json_file_path = "sauvegarde.json"
    # with open(json_file_path, 'w', encoding='utf-8') as f:
    #     json.dump(project_dict, f, ensure_ascii=False, indent=4)

    cur.close()
    con.close()

    response = make_response(jsonify(project_dict))
    response.headers['Content-Disposition'] = f'attachment; filename={project_name}.json'
    response.headers['Content-Type'] = 'application/json'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'

    return response

def project_load_json():
    if 'json_file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['json_file']
    if file.filename == '':
        return 'No file selected', 400

    try:
        filename = "tempo.json"
        json_file_path=os.path.join(PDF_UPLOAD_PATH, filename)
        #json_file_path = tempfile.NamedTemporaryFile(delete=False, suffix='.json').name

        file.save(json_file_path)
        load_json(json_file_path)
        return redirect("/")

    except Exception as e:
        return f'Error processing file: {str(e)}', 500


def load_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as f:
        project_dict = json.load(f)

    json_file_name = os.path.basename(json_file_path)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    # project

    # new_project_name = (project_dict['name'] + " (loaded from '" + json_file_name + "' at " + time.strftime("%Y-%m-%d %H:%M:%S") + ")")
    new_project_name = (project_dict['name'] + " (loaded " + time.strftime("%Y-%m-%d %H:%M:%S") + ")")

    sql = "INSERT INTO projects (name, eligibility_criteria, green_words, red_words, type_of_study) VALUEs (?,?,?,?,?)"
    parameters = (new_project_name, project_dict['eligibility_criteria'], project_dict['green_words'],
                  project_dict['red_words'], project_dict['type_of_study'])
    cur.execute(sql, parameters)
    con.commit()
    new_project_id = cur.lastrowid

    # fields
    fields_new_id = dict()  # key old value = new id dans ce new project
    for f in project_dict["fields"]:
        sql = "INSERT INTO study_fields (name, description, category, sort_order, project) VALUES (?,?,?,?,?)"
        parameters = (f['name'], f['description'], f['category'], f['sort_order'], new_project_id)
        cur.execute(sql, parameters)
        con.commit()
        fields_new_id[f['id']] = cur.lastrowid

    # studies
    study_new_id = dict()
    for study in project_dict['studies']:
        sql = "INSERT INTO studies (name, registration_number, project) VALUES (?,?,?)"
        parameters = (study['name'], study['registration_number'], new_project_id)
        cur.execute(sql, parameters)
        con.commit()
        study_id = cur.lastrowid
        study_new_id[study['id']] = study_id

        # study records
        for r in study['records']:
            sql = "INSERT INTO records (pmid, DOI, source, abstract, search, AI_decision, AI_answer, url, registration_number, acronym, author1, title, selection, exclusion_reason, database,  project) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
            parameters = (r['pmid'], r['DOI'], r['source'], r['abstract'], r['search'], r['AI_decision'],
                          r['AI_answer'], r['url'], r['registration_number'], r['acronym'], r['author1'],
                          r['title'], r['selection'], r['exclusion_reason'], r['database'], new_project_id)
            cur.execute(sql, parameters)
            con.commit()
            record_id = cur.lastrowid
            sql = "INSERT INTO rel_study_records (study, record) VALUES (?,?)"
            parameters = (study_id, record_id)
            cur.execute(sql, parameters)
            con.commit()

        # study data
        for f in study['fields']:
            sql = "INSERT INTO study_field_values (study, field, value) VALUES (?,?,?)"
            parameters = (study_id, fields_new_id[f['field']], f['value'])
            cur.execute(sql, parameters)

    for r in project_dict['unselected_records']:
        sql = "INSERT INTO records (pmid, DOI, source, abstract, search, AI_decision, AI_answer, url, registration_number, acronym, author1, title, selection, exclusion_reason, database,  project) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
        parameters = (r['pmid'], r['DOI'], r['source'], r['abstract'], r['search'], r['AI_decision'],
                      r['AI_answer'], r['url'], r['registration_number'], r['acronym'], r['author1'],
                      r['title'], r['selection'], r['exclusion_reason'], r['database'], new_project_id)
        cur.execute(sql, parameters)
        con.commit()
        record_id = cur.lastrowid

    cur.close()
    con.close()



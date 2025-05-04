import sqlite3
import os
import json

DB_PATH = "srai_database.sqlite"



def save_project(project_id):

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

    sql="""
    SELECT *
    FROM study_fields
    WHERE project=?
    """
    d = get_dictionary_rows(sql, (project_id,))
    project_dict['fields'] = d


    # studies
    sql = "SELECT * FROM STUDIES WHERE project=?"
    cur.execute(sql,(project_id,))
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
              WHERE rel_study_records.study=?
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
        WHERE study_field_values.study=?
        """
        d = get_dictionary_rows(sql, (study_id,))
        study_dict['fields'] = d

        studies_dict.append(study_dict)
        #print(studies_dict)
        project_dict['studies'] = studies_dict


    # records without study
    sql = """
          SELECT records.* 
          FROM records 
              LEFT JOIN rel_study_records ON rel_study_records.record = records.id
          WHERE records.project=? AND rel_study_records.study IS NULL
          """
    d = get_dictionary_rows(sql, (project_id,))
    for e in d:
        if isinstance(e['AI_answer'], bytes):
            e['AI_answer'] = e['AI_answer'].decode('utf-8')

    project_dict['unselected_records'] = d


    ### save json file
    json_file_path = "sauvegarde.json"
    with open(json_file_path, 'w', encoding='utf-8') as f:
        json.dump(project_dict, f, ensure_ascii=False, indent=4)


    cur.close()
    con.close()

save_project(1)
import json
import sqlite3
import time
from utils import DB_PATH


json_file_path = "C:\\Users\\miche\\Downloads\\sotorasib for NSCLC.json"
json_file_name = json_file_path.split("\\")[-1]

with open(json_file_path, 'r', encoding='utf-8') as f:
    project_dict = json.load(f)

con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
cur = con.cursor()

#project
new_project_name = (project_dict['name'] + " (loaded from '" + json_file_name + "' at " + time.strftime("%Y-%m-%d %H:%M:%S") +")")
sql = "INSERT INTO projects (name, eligibility_criteria, green_words, red_words, type_of_study) VALUEs (?,?,?,?,?)"
parameters = (new_project_name, project_dict['eligibility_criteria'], project_dict['green_words'], project_dict['red_words'], project_dict['type_of_study'])
cur.execute(sql, parameters)
con.commit()
new_project_id = cur.lastrowid

#fields
fields_new_id = dict() #key old value = new id dans ce new project
for f in project_dict["fields"]:
    sql = "INSERT INTO study_fields (name, description, category, project) VALUES (?,?,?,?)"
    parameters = (f['name'], f['description'], f['category'], new_project_id)
    cur.execute(sql, parameters)
    con.commit()
    fields_new_id[f['id']] = cur.lastrowid

# studies
study_new_id = dict()
for study in project_dict['studies']:
    sql= "INSERT INTO studies (name, registration_number, project) VALUES (?,?,?)"
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
        sql= "INSERT INTO study_field_values (study, field, value) VALUES (?,?,?)"
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



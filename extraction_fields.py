import sqlite3
from flask import Flask, render_template, request, redirect, url_for

import os, json
import re

from utils import *

def extraction_field_edit(field_id, project_id):
    sql = "SELECT * FROM study_fields WHERE id=?"
    field_data = sql_select_fetchone(sql, (field_id,))
    return render_template('extraction_field_edit.html', field_id=field_id, field_data=field_data, project_id=project_id)



def extraction_field_add(project_id):
    sql = "INSERT INTO study_fields (name, description, project) VALUES (?,?,?)"
    field_id = sql_insert_into(sql, ("new field","Give a short description for the AI extraction tool", project_id))
    return redirect(url_for("endpoint_extraction_field_edit", field_id=field_id, project_id=project_id))



def extraction_field_delete(field_id, project_id):
    sql = "DELETE FROM study_fields WHERE id=?"
    sql_delete(sql, (field_id,))
    return "", 200


def load_standard_fields_file(file, project_id):
    if file=="RCT":
        filename="standard_fields_RCT.json"
    elif file=="OBS":
        filename="standard_fields_OBS.json"
    elif file=="DIAG":
        filename="standard_fields_DIAG.json"
    else:
        return None

    # base_dir = os.path.dirname(os.path.abspath(__file__))
    # file_path = os.path.join(base_dir, 'standard_fields_RCT.txt')
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
    except Exception as e:
        print(f"Erreur lors de la lecture du fichier : {e}")
        return None

    for f in data:
        sql = "INSERT INTO study_fields (name, description, project) VALUES (?,?,?)"
        sql_insert_into(sql, (f['name'], f['description'], project_id))

    return redirect(url_for("endpoint_project_extraction_fields_list", project_id=project_id))

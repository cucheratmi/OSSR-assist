import sqlite3
import os
from enum import IntEnum
from dotenv import load_dotenv
from pathlib import Path


DB_PATH = "srai_database.sqlite"

PDF_UPLOAD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdf')

BIBLIOGRAPHIC_DATABASE = {'Pubmed': 1,'Embase': 2, 'Endnote':97, 'Other': 98, 'Manually': 99}

ROB_RCT_DOMAIN = {
    1:'bias arising from the randomization process',
    2:'bias due to deviations from intended interventions',
    3:'bias due to missing outcome data',
    4:'bias in measurement of the outcome',
    5:'bias in selection of the reported result'
}
ROB_DIAG_DOMAIN = {
    1:'Bias patient selection',
    2:'Applicability patient selection',
    3:'Bias index test(s)',
    4:'Applicability index test(s)',
    5:'Bias in reference standard',
    6:'Applicability reference standard',
    7:'Bias flow and timing'
}

OUTCOMES_TYPES = {
    1:'binary',
    2:'continuous',
    99:'other'
}

class InclusionStatus(IntEnum):
    PENDING = 0
    UNDECIDED = 1
    INCLUDED_FIRST_PASS = 2
    INCLUDED_SECOND_PASS = 3
    EXCLUDED_FIRST_PASS = 4
    EXCLUDED_SECOND_PASS = 5

INCLUSION_STATUS_DICT = dict()
INCLUSION_STATUS_DICT[InclusionStatus.PENDING.value] = "Pending"
INCLUSION_STATUS_DICT[InclusionStatus.UNDECIDED.value] = "Undecided"
INCLUSION_STATUS_DICT[InclusionStatus.INCLUDED_FIRST_PASS.value] = "Included (first pass)"
INCLUSION_STATUS_DICT[InclusionStatus.INCLUDED_SECOND_PASS.value] = "Included (second pass)"
INCLUSION_STATUS_DICT[InclusionStatus.EXCLUDED_FIRST_PASS.value] = "Excluded (first pass)"
INCLUSION_STATUS_DICT[InclusionStatus.EXCLUDED_SECOND_PASS.value] = "Excluded (second pass)"


class ExclusionReason(IntEnum):
    WRONG_POPULATION=1
    WRONG_TREATMENT=2
    WRONG_CONTROL=3
    WRONG_DESIGN=4
    WRONG_OBJECTIVE=5
    NOT_A_PUBLICATION_ABOUT_A_STUDY=6
    OTHER=7
    WRONG_OUTCOME=8

EXCLUSION_REASON_DICT = dict()
EXCLUSION_REASON_DICT[0] = ""
EXCLUSION_REASON_DICT[ExclusionReason.WRONG_POPULATION.value] = "Wrong population"
EXCLUSION_REASON_DICT[ExclusionReason.WRONG_TREATMENT.value] = "Wrong treatment"
EXCLUSION_REASON_DICT[ExclusionReason.WRONG_CONTROL.value] = "Wrong control"
EXCLUSION_REASON_DICT[ExclusionReason.WRONG_DESIGN.value] = "Wrong design"
EXCLUSION_REASON_DICT[ExclusionReason.WRONG_OBJECTIVE.value] = "Wrong objective"
EXCLUSION_REASON_DICT[ExclusionReason.NOT_A_PUBLICATION_ABOUT_A_STUDY.value] = "Not a publication about a study"
EXCLUSION_REASON_DICT[ExclusionReason.OTHER.value] = "Other"
EXCLUSION_REASON_DICT[ExclusionReason.WRONG_OUTCOME.value] = "Wrong outcome"


class TypeOfStudy(IntEnum):
    OBS=1
    RCT=2
    DIAG=3
    OTHER=4
    MA=5

type_of_study_dict = {
    1: "OBS",
    2: "RCT",
    3: "DIAG",
    4: "OTHER",
    5: "MA"
}


### htmlx utilities

def update_field(table, id, field, value):

    assert table in ["studies", "records", "projects","study_fields","outcomes"]
    assert field is not None
    assert value is not None
    assert id is not None

    value = value.strip()

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    sql = f"UPDATE {table} SET {field}=? WHERE id=?"
    print(f"{table}.{field} = {value} {id=}")
    cur.execute(sql, (value, id))
    con.commit()
    cur.close()
    con.close()

    l = f"saved! {table}.{field} = {value}"
    return l


def htmlx_update_field(table, id, data):
    field, value = next(iter(data.items()))
    return update_field(table, id, field, value)

def htmlx_update_field2(study_id, field_id, data):
    field = f"F{field_id}"
    value = data[field]
    l =f"{field} = {value}"
    print(l)

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    sql = "INSERT OR REPLACE INTO study_field_values (study, field, value) VALUES (?, ?, ?)"
    cur.execute(sql, (study_id, field_id, value,))
    con.commit()

    cur.close()
    con.close()

    return l


### sql utilities

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Pour avoir les résultats sous forme de dictionnaire
    return conn

def sql_select_fetchone(sql, parameters):
    with get_db_connection() as con:
        cur = con.cursor()
        res = cur.execute(sql, parameters)
        r = res.fetchone()
    return r

def sql_select_fetchall(sql, parameters):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    res = cur.execute(sql, parameters)
    rows = res.fetchall()

    columns = [column[0] for column in cur.description]
    result = [dict(zip(columns, row)) for row in rows]

    cur.close()
    con.close()

    return result

def sql_update(sql, parameters):
    assert "DELETE" not in sql
    assert "delete" not in sql

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, parameters)
    con.commit()
    cur.close()
    con.close()

def sql_insert_into(sql, parameters):
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, parameters)
    con.commit()
    id = cur.lastrowid
    cur.close()
    con.close()
    return id


def sql_delete(sql, parameters):
    con = sqlite3.connect(DB_PATH)
    #con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(sql, parameters)
    con.commit()
    cur.close()
    con.close()


##########################

def get_references(study_id):
    sql="""
        SELECT id, author1, title, source, pmid, DOI, abstract 
        FROM records
            INNER JOIN rel_study_records ON rel_study_records.record = records.id
        WHERE rel_study_records.study=?
        """
    references = sql_select_fetchall(sql,(study_id,))
    references_dict = {ref['id']: ref for ref in references}
    return references_dict


def get_project_name(project_id):
    sql="SELECT name, type_of_study, eligibility_criteria FROM projects WHERE id=?"
    r = sql_select_fetchone(sql, (project_id,))
    project_name = r['name']
    study_type = r['type_of_study']
    eligibility_criteria_empty = (r['eligibility_criteria'] is None or r['eligibility_criteria'].strip() == "")
    return project_name, study_type, eligibility_criteria_empty


def is_outcomes_list_empty(project_id):
    sql = "SELECT COUNT(*) FROM outcomes WHERE project=?"
    parameters = (project_id,)
    return sql_select_fetchone(sql, parameters)['COUNT(*)'] == 0

def is_extraction_fields_list_empty(project_id):
    sql = "SELECT COUNT(*) FROM study_fields WHERE project=?"
    parameters = (project_id,)
    return sql_select_fetchone(sql, parameters)['COUNT(*)'] == 0




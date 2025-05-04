import sqlite3
import os
import json

DB_PATH = "srai_database.sqlite"

ROB_DOMAIN = {
    1:'bias arising from the randomization process',
    2:'bias due to deviations from intended interventions',
    3:'bias due to missing outcome data',
    4:'bias in measurement of the outcome',
    5:'bias in selection of the reported result'
}

con = sqlite3.connect(DB_PATH)
con.row_factory = sqlite3.Row
cur = con.cursor()


sql ="""
    SELECT studies.name AS study_name, ROB_values.domain AS domain, ROB_values.level AS level, ROB_values.justification AS justification
    FROM studies
             INNER JOIN ROB_values ON ROB_values.study = studies.id
    WHERE studies.project =?
    ORDER BY studies.name, rob_values.domain \
    """
cur.execute(sql, (1,))
rows = cur.fetchall()

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
        for i in range(1,6):
            rob[i] = {'domain': ROB_DOMAIN[i], 'level': None, 'justification': None}

    domain = r['domain']
    level = r['level']
    justification = r['justification']

    rob[domain]['level'] = level
    rob[domain]['justification'] = justification

study['rob'] = rob
studies.append(study)

html = ""
html += "<tr><th rowspan='2'>Study</th>"
for i in range(1,6):
    html += "<th colspan='2'>" + ROB_DOMAIN[i] + "</th>"
html += "</tr>\n"

html += "<tr>"
for i in range(1,6):
    html += "<td>Level</td><td>Justification</td>"
html += "</tr>\n"

for study in studies:
    html += "<tr>"
    html += "<td>" + study['study_name'] +"</td>"

    for i in range(1,6):
        match study['rob'][i]['level']:
            case 1: level = "Low"
            case 2: level = "Medium"
            case 3: level = "High"
            case _: level = ""

        justification = study['rob'][i]['justification']
        html += "<td>" + level + "</td><td>" + justification + "</td>"

    html += "</tr>\n"

print("ZZZZ" + html)


cur.close()
con.close()

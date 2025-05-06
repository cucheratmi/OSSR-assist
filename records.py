import sqlite3

from flask import Flask, render_template, request, redirect, url_for, send_file,current_app, flash

import re, math
import csv, io
import datetime

from AI_utils import is_primary_LLM_available, is_secondary_LLM_available
from utils import *
from pubmed import parse_pubmed_file
#from AI_screening import AI_records_screening

def reset_selection(record_id, project_id, pass_number):
    sql = "UPDATE records SET selection=? WHERE id=?"
    sql_update(sql, (0, record_id,))

    return redirect(url_for("endpoint_records_list", project_id=project_id, pass_number=pass_number))

def records_list(project_id, pass_number=1, page=1):
    PAGE_SIZE=10

    sql = """
          SELECT id, pmid, doi, source, title, author1, registration_number, AI_decision, AI_answer, abstract, selection 
             FROM records WHERE project=?
          """
    and_where = ""
    if pass_number==2: and_where = "AND selection=" + str(InclusionStatus.UNDECIDED.value)

    sql = f"SELECT COUNT(id) AS k FROM records WHERE project=? {and_where}"
    rs = sql_select_fetchone(sql, (project_id,))
    n_records = rs['k'] if rs is not None else 0
    npage = math.ceil(int(n_records) / PAGE_SIZE)

    first_reference=(page-1)*PAGE_SIZE+1
    last_reference=page*PAGE_SIZE
    last_reference=min(last_reference, n_records)
    n_reference=n_records


    sql2 = f"""
    SELECT id 
    FROM records 
    WHERE project=? {and_where} 
    ORDER BY selection, AI_decision DESC, id 
    LIMIT {PAGE_SIZE} OFFSET {(page-1) * PAGE_SIZE}
    """

    sql = f"""
    SELECT records.*, studies.name AS study_name, studies.registration_number AS study_registration_number, studies.id AS study_id 
    FROM records
        LEFT JOIN rel_study_records ON rel_study_records.record = records.id
        LEFT JOIN studies ON studies.id = rel_study_records.study
    WHERE records.id IN ({sql2})
    ORDER BY records.selection, records.AI_decision DESC, records.id
    """

    records = sql_select_fetchall(sql, (project_id,))

    project_name, study_type, eligibility_criteria_empty = get_project_name(project_id)

    database_dict = {valeur: cle for cle, valeur in BIBLIOGRAPHIC_DATABASE.items()}

    for e in records:
        e["database"] = database_dict[e["database"]] if e["database"] in database_dict else "unknown"

        e["AI_answer"] = format_AI_screening_suggestion(e["AI_answer"])

        if e["abstract"] is None: e["abstract"] = ""
        e["abstract"] = e["abstract"].replace('"','\'')

        x = int(e["AI_decision"])
        if x==1: e["AI_decision"] = "<i class='bi bi-check' style='color: forestgreen; font-size: 2rem;'></i>"
        if x==0: e["AI_decision"] = "<i class='bi bi-question' style='color: orange; font-size: 2rem;'></i>"
        if x==-1: e["AI_decision"] = "<i class='bi bi-x' style='color: red; font-size: 2rem;'></i>"

        selection_class = ""
        if e["selection"]==InclusionStatus.EXCLUDED_FIRST_PASS.value or e["selection"]==InclusionStatus.EXCLUDED_SECOND_PASS.value:
            selection_class = "table-danger"
        if e["selection"]==InclusionStatus.INCLUDED_FIRST_PASS.value or e["selection"]==InclusionStatus.INCLUDED_SECOND_PASS.value:
            selection_class = "table-success"
        if e["selection"]==InclusionStatus.UNDECIDED.value:
            selection_class = "table-warning"
        e["selection_class"] = selection_class

        e["selection_text"] = INCLUSION_STATUS_DICT[e["selection"]]
        e["exclusion_reason_text"] = EXCLUSION_REASON_DICT[e["exclusion_reason"]]

        if (e['selection']==InclusionStatus.INCLUDED_FIRST_PASS or e['selection']==InclusionStatus.INCLUDED_SECOND_PASS) and e['study_id'] is None:
            e["study_name"] = "create study"

    #primary_LLM_available = is_primary_LLM_available()

    return render_template('records_list.html', project_id=project_id, project_name=project_name, records=records,
                           pass_number=pass_number, i_page=page, n_page=npage,
                           first_reference=first_reference, last_reference=last_reference, n_reference=n_reference,
                           primary_LLM_available=is_primary_LLM_available(), eligibility_criteria_empty=eligibility_criteria_empty)


def format_AI_screening_suggestion(s):
    if s is None: return ""
    if type(s) is str:
        s = s.replace('\n', "<br/>").replace('"','\'')
    else:
        s = s.decode('utf-8').replace('\n', "<br/>").replace('"','\'')
    s = s.replace('\n', "<br/>")
    s = re.sub(r'\bstudy is eligible\b', f"<span style='color: green; font-weight: bold;'>study is eligible</span>", s, flags=re.IGNORECASE)
    s = re.sub(r'\bstudy is not eligible\b', f"<span style='color: red; font-weight: bold;'>study is not eligible</span>", s, flags=re.IGNORECASE)
    return s

def records_upload_form(project_id, s_database):
    sql="SELECT name FROM projects WHERE id=?"
    project_name = sql_select_fetchone(sql, (project_id,))['name']
    return render_template('records_upload_form.html', project_id=project_id, project_name=project_name, s_database=s_database)


def records_upload(project_id, s_database):
    if 'risFile' not in request.files:
        return 'No file uploaded', 400

    file = request.files['risFile']

    if file.filename == '':
        return 'No file selected', 400

    try:
        match s_database:
            case "endnote":
                database = BIBLIOGRAPHIC_DATABASE["Endnote"]
                s_database = "Endnote file"
                app_dir = os.path.dirname(os.path.abspath(__file__))
                file_path = app_dir + "/tempo/endnote.txt"
                file.save(file_path)

                return render_template('streaming_read_references.html', project_id=project_id, database=database, s_database=s_database)

            case _:
                database = BIBLIOGRAPHIC_DATABASE["Pubmed"]
                content = file.read().decode('utf-8')
                parse_pubmed_file(content, project_id)
                return redirect(url_for('endpoint_records_list', project_id=project_id))

    except Exception as e:
        return f'Error processing file: {str(e)}', 500


def highlight(s, green_words, red_words):
    if s is not None:
        for word in red_words:
            if word=="": continue
            s = re.sub(r'\b'+word+r'\b', f"<span class='red_word'>{word}</span>", s, flags=re.IGNORECASE)

        for word in green_words :
            if word=="": continue
            s = re.sub(r'\b'+word+r'\b', f"<span class='green_word'>{word}</span>", s, flags=re.IGNORECASE)

    return s

def records_screening_window(record_id, project_id, pass_number):
    if pass_number==1:
        template_file = "records_screening_pass1_window.html"
    else:
        template_file = "records_screening_pass2_window.html"

    sql="""
    SELECT records.*, studies.name AS study_name, studies.registration_number AS study_registration_number, studies.id AS study_id 
    FROM records
        LEFT JOIN rel_study_records ON rel_study_records.record = records.id
        LEFT JOIN studies ON studies.id = rel_study_records.study
    WHERE records.id=?
    """
    record_data = sql_select_fetchone(sql, (record_id,))
    record_data = dict(record_data)
    project_id = record_data["project"]

    sql = "SELECT id, name, registration_number FROM studies WHERE project=? ORDER BY name"
    included_studies = sql_select_fetchall(sql, (project_id,))

    sql = "SELECT red_words, green_words, eligibility_criteria FROM projects WHERE id=?"
    project_data = sql_select_fetchone(sql, (project_id,))

    ### highlight abstract with green and red words
    red_words = project_data["red_words"].split("\n")
    green_words = project_data["green_words"].split("\n")
    eligibility_criteria = project_data["eligibility_criteria"]
    eligibility_criteria = eligibility_criteria.replace('\n', '<br/>')

    record_data["abstract"] = highlight(record_data["abstract"], green_words, red_words)
    record_data["title"] = highlight(record_data["title"], green_words, red_words)

    pdf_file_name = os.path.join(PDF_UPLOAD_PATH, f"r{record_id}.pdf")
    pdf_exists = os.path.exists(pdf_file_name)

    ### search acronym of already known studies
    known_study = None
    for study in included_studies:
        if study["registration_number"] is not None and study["registration_number"]!="":
            if (study["registration_number"].lower() in record_data["abstract"].lower()) or (study["registration_number"].lower()==record_data["registration_number"].lower()):
                known_study = study
                break
        if study["name"] is not None and study["name"]!="":
            if study["name"].lower() in (record_data["abstract"]+ " " + record_data["title"]).lower():
                known_study = study
                break

    ### format AI answer
    record_data["AI_answer"] = format_AI_screening_suggestion(record_data["AI_answer"])

    ### button style
    btn_exclude_style = "color: red; width: 50%;"
    btn_exclude_label = "exclude"
    if record_data["selection"]==InclusionStatus.EXCLUDED_FIRST_PASS.value or record_data["selection"]==InclusionStatus.EXCLUDED_SECOND_PASS.value:
        btn_exclude_style = "background-color: red; color: white; width: 50%;"
        btn_exclude_label = "excluded"

    btn_include_style = "color: green; width: 50%;"
    btn_include_label = "include"
    if record_data["selection"] == InclusionStatus.INCLUDED_FIRST_PASS.value or record_data["selection"] == InclusionStatus.INCLUDED_SECOND_PASS.value:
        btn_include_style = "background-color: green; color: white; width: 50%;"
        btn_include_label = "included"

    btn_undecided_style = "color: dimgray; width: 50%;"
    btn_undecided_label = "maybe"
    if record_data["selection"] == InclusionStatus.UNDECIDED.value:
        btn_undecided_style = "background-color: dimgray; color: white; width: 50%;"
        btn_undecided_label = "set maybe"

    return render_template(
        template_file,
        record_id=record_id, project_id=project_id, record_data=record_data, pass_number=pass_number,
        included_studies=included_studies, project_data=project_data, known_study=known_study,
        btn_exclude_style=btn_exclude_style, btn_include_style=btn_include_style, btn_undecided_style=btn_undecided_style,
        btn_exclude_label=btn_exclude_label, btn_include_label=btn_include_label, btn_undecided_label=btn_undecided_label,
        exclusion_reason = ExclusionReason, pdf_exists=pdf_exists, eligibility_criteria=eligibility_criteria
    )



def records_screening_pass1_next(record_id, project_id):
    sql = "SELECT id FROM records WHERE project=? AND selection=0 AND id>? ORDER BY id LIMIT 1"
    rs = sql_select_fetchone(sql, (project_id, record_id,))
    if rs is None:
        return redirect(url_for("endpoint_records_list", project_id=project_id))
    record_id = rs['id']
    return redirect(url_for("endpoint_records_screening_pass1_window",  record_id=record_id, project_id=project_id))

def records_screening_pass2_next(record_id, project_id):
    sql = f"SELECT id FROM records WHERE project=? AND selection={InclusionStatus.UNDECIDED} AND id>? ORDER BY id LIMIT 1"
    rs = sql_select_fetchone(sql, (project_id, record_id,))
    if rs is None:
        return redirect(url_for("endpoint_records_list", project_id=project_id, pass_number=2, page=1 ))
    record_id = rs['id']
    return redirect(url_for("endpoint_records_screening_pass2_window",  record_id=record_id, project_id=project_id))


def record_create_study(project_id, record_id, pass_number):
    assert project_id is not None
    assert project_id != 0

    study_id = create_study_from_record(project_id, record_id, InclusionStatus.INCLUDED_FIRST_PASS)

    sql = "SELECT * FROM studies WHERE id=?"
    study_data = sql_select_fetchone(sql, (study_id,))

    sql="SELECT * FROM records WHERE id=?"
    record_data = sql_select_fetchone(sql, (record_id,))
    #convert sqlite3.Row into ordinary dictionary
    record_data = dict(record_data)
    # project_id = record_data["project"]

    #TODO à supprimer
    # ### format AI answer
    # if record_data["AI_answer"] is not None:
    #     if isinstance(record_data['AI_answer'], bytes):
    #         s = record_data["AI_answer"].decode('utf-8')
    #     else:
    #         s = record_data["AI_answer"]
    #
    #     s = s.replace('\n\n', '<br/>')
    #     s = re.sub(r'\bstudy is eligible\b', f"<span style='color: green; font-weight: bold;'>study is eligible</span>",
    #                s, flags=re.IGNORECASE)
    #     s = re.sub(r'\bstudy is not eligible\b',
    #                f"<span style='color: red; font-weight: bold;'>study is not eligible</span>", s, flags=re.IGNORECASE)
    #     record_data["AI_answer"] = s.replace('\n', "<br/>").replace('"', '\'')
    #
    # ### references linked to this study
    # sql="""
    #     SELECT id, author1, title, source, pmid, DOI
    #     FROM records
    #         INNER JOIN rel_study_records ON rel_study_records.record = records.id
    #     WHERE rel_study_records.study=?
    #     """
    # references = sql_select_fetchall(sql,(study_id,))


    flash(make_message_study_created(study_id, study_data['name']), 'success')

    if pass_number==2:
        return redirect(url_for("endpoint_records_screening_pass2_window", record_id=record_id, project_id=project_id))
    else:
        return redirect(url_for("endpoint_records_screening_pass1_window", record_id=record_id, project_id=project_id))

def make_message_study_created(study_id, study_name):
    mssg = f"""
    <h4 class="alert-heading mb-3"><i class="bi bi-check-circle"></i> Study created!</h4>
    <form style="background-color: white;" class="p-4">
        <label for="name" class="form-label">Name</label>
        <input type="text" class="form-control" id="name" name="name" value="{ study_name }"
               hx-post="/study/update_field/{ study_id }/name" hx-trigger="change" hx-target="#name_info"
               hx-swap="innerHTML"/>
        <div class="form-text">Study name: acronym or first author, year</div>
        <div id="name_info" class="form-text"></div>
    </form>
    """
    return mssg

def records_screening_set_included(record_id, selection, pass_number, project_id):
    if selection == "undecided": selection_value=InclusionStatus.UNDECIDED.value
    elif selection == "included_first_pass": selection_value = InclusionStatus.INCLUDED_FIRST_PASS.value
    elif selection == "excluded_first_pass": selection_value = InclusionStatus.EXCLUDED_FIRST_PASS.value
    elif selection == "included_second_pass": selection_value = InclusionStatus.INCLUDED_SECOND_PASS.value
    elif selection == "excluded_second_pass": selection_value = InclusionStatus.EXCLUDED_SECOND_PASS.value
    else: return "error"
    sql = "UPDATE records SET selection=? WHERE id=?"
    sql_update(sql, (selection_value, record_id))

    if pass_number==1:
        return redirect(url_for("endpoint_records_screening_pass1_window",  record_id=record_id, project_id=project_id))
    else:
        return redirect(url_for("endpoint_records_screening_pass2_window",  record_id=record_id, project_id=project_id))


def records_screening_set_excluded(record_id, exclusion_reason, pass_number, project_id):
    if pass_number==1:
        selection_value = InclusionStatus.EXCLUDED_FIRST_PASS.value
    else:
        selection_value = InclusionStatus.EXCLUDED_SECOND_PASS.value

    sql = "UPDATE records SET selection=?, exclusion_reason=? WHERE id=?"
    sql_update(sql, (selection_value, exclusion_reason, record_id))

    if pass_number==1:
        return redirect(url_for("endpoint_records_screening_pass1_window",  record_id=record_id, project_id=project_id))
    else:
        return redirect(url_for("endpoint_records_screening_pass2_window",  record_id=record_id, project_id=project_id))


def create_study_from_record(project_id, record_id, screening_pass):
    sql = "SELECT author1, registration_number, acronym FROM records WHERE id=?"
    record_data = sql_select_fetchone(sql, (record_id,))
    study_name = ""
    registration_number = record_data["registration_number"]
    if registration_number is None: registration_number = ""
    if record_data["acronym"] is not None: study_name = record_data["acronym"]
    if study_name == "": study_name = registration_number
    if study_name == "": study_name = record_data["author1"]
    if study_name == "": study_name = "new study"

    sql = "INSERT INTO studies (name, project, registration_number) VALUES (?,?,?)"
    study_id = sql_insert_into(sql, (study_name, project_id, registration_number))

    sql = "INSERT INTO rel_study_records (record, study) VALUES (?,?)"
    x = sql_insert_into(sql, (record_id, study_id))

    sql = f"UPDATE records SET selection=? WHERE id=?"
    sql_update(sql, (screening_pass.value, record_id,))

    return study_id


def record_study_add(project_id, record_id):
    study_id = create_study_from_record(project_id, record_id, InclusionStatus.INCLUDED_SECOND_PASS)
    return redirect(url_for("endpoint_study_edit", study_id=study_id, project_id=project_id))

def record_link_to_study(project_id, record_id, study_id):
    sql = "INSERT OR IGNORE INTO rel_study_records (record, study) VALUES (?,?)"
    x = sql_insert_into(sql, (record_id,study_id))
    return redirect(url_for("endpoint_study_edit", project_id=project_id, study_id=study_id))


def link_record_to_study(record_id, study_id, pass_number):
    sql = "INSERT OR IGNORE INTO rel_study_records (record, study) VALUES (?,?)"
    x = sql_insert_into(sql, (record_id, study_id))

    v = InclusionStatus.INCLUDED_FIRST_PASS.value if pass_number==1 else InclusionStatus.INCLUDED_SECOND_PASS.value
    sql = f"UPDATE records SET selection=? WHERE id=?"
    sql_update(sql, (v, record_id,))

    return redirect(url_for("endpoint_records_screening_pass1_window",  record_id=record_id))

def delete_AI_suggestions(project_id):
    sql="UPDATE records SET AI_answer='', AI_decision=0 WHERE project=?"
    sql_update(sql, (project_id,))

    return redirect(url_for("endpoint_records_list",  project_id=project_id))


def records_delete(project_id):
    sql = "DELETE FROM records WHERE project=? AND id NOT IN (SELECT record FROM rel_study_records WHERE study IN (SELECT id FROM studies WHERE project=?))"
    sql_delete(sql, (project_id,project_id,))

    return redirect(url_for("endpoint_records_list", project_id=project_id))


def records_export_CSV(project_id):
    sql = "SELECT * FROM records WHERE project=?"
    records = sql_select_fetchall(sql, (project_id,))

    # Créer un buffer en mémoire pour écrire le CSV
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=records[0].keys())

    # Écrire l'en-tête
    writer.writeheader()

    # Écrire les lignes
    for record in records:
        record["selection"] = INCLUSION_STATUS_DICT[record["selection"]]
        record["exclusion_reason"] = EXCLUSION_REASON_DICT[record["exclusion_reason"]]
        writer.writerow(dict(record))

    # Préparer le fichier pour l'envoi
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'references_project_{project_id}.csv'
    )

def records_export_RIS(project_id):

    def write_ris_line(tag, value):
        # Fonction helper pour écrire une ligne RIS
        if value is not None and value != "":
            output.write(f"{tag}  - {value}\n")
            


    sql = "SELECT * FROM records WHERE project=?"
    records = sql_select_fetchall(sql, (project_id,))
    current_date =  datetime.datetime.now().strftime("%Y/%m/%d")

    output = io.StringIO()


    for record in records:
        output.write("TY  - JOUR\n")

        # Auteurs (AU)
        write_ris_line("AU", record['author1'])

        # Titre (TI)
        write_ris_line("TI", record['title'])

        # Journal/Source (JO)
        write_ris_line("JO", record['source'])

        # DOI
        write_ris_line("DO", record['DOI'])

        # PMID
        write_ris_line("AN", record['pmid'])

        # Numéro d'enregistrement
        write_ris_line("M1", record['registration_number'])

        # Abstract (AB)
        write_ris_line("AB", record['abstract'])

        write_ris_line("N1", INCLUSION_STATUS_DICT[record['selection']] + " " + EXCLUSION_REASON_DICT[record['exclusion_reason']])

        write_ris_line("KW", INCLUSION_STATUS_DICT[record['selection']])
        write_ris_line("KW", EXCLUSION_REASON_DICT[record['exclusion_reason']])

        # Date d'export (DA)
        write_ris_line("DA", current_date)

        # Fin d'enregistrement
        output.write("ER  - \n\n")

    # Préparer le fichier pour l'envoi
    output.seek(0)

    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='application/x-research-info-systems',
        as_attachment=True,
        download_name=f'references_project_{project_id}.ris'
    )

def records_flowchart(project_id):
    total=0
    included1=0
    excluded1=0
    included2=0
    excluded2=0
    undecided=0
    pending = 0
    studies=0

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=0"
    total = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=1"
    included1 = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=2"
    included2 = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=-1"
    excluded1 = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=-2"
    excluded2 = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=5"
    undecided = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql = "SELECT COUNT(*) FROM records WHERE project=? AND selection=0"
    pending = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    sql="SELECT COUNT(*) FROM studies WHERE project=?"
    studies = sql_select_fetchone(sql, (project_id,))['COUNT(*)']

    return render_template('records_flowchart.html', project_id=project_id, pending=pending, total=total,
                           included1=included1, excluded1=excluded1, included2=included2, excluded2=excluded2,
                           undecided=undecided, studies=studies)


def record_edit(record_id, project_id):
    sql = "SELECT * FROM records WHERE id=?"
    record_data = sql_select_fetchone(sql, (record_id,))

    return render_template('record_edit.html',record_data=record_data, record_id=record_id, project_id=project_id)
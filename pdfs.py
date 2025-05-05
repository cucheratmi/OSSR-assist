import sqlite3
import os
from flask import Flask, render_template, request, redirect, url_for


from utils import *

def test_if_pdf_exists(record_id):
    if record_id is None: return False
    pdf_file_name = os.path.join(PDF_UPLOAD_PATH, f"r{record_id}.pdf")
    return os.path.exists(pdf_file_name)

def pdfs_list(project_id, record_id):
    project_name, study_type, eligibility_criteria_empty = get_project_name(project_id)

    l = [InclusionStatus.INCLUDED_FIRST_PASS.value, InclusionStatus.INCLUDED_SECOND_PASS.value, InclusionStatus.UNDECIDED.value]
    s = ",".join(str(x) for x in l)

    sql = f"""
    SELECT id,author1,source, pmid, DOI, selection FROM records WHERE project=? AND selection IN({s})
    """
    references = sql_select_fetchall(sql, (project_id,))
    pdf_exists=dict()
    pdf_paths=dict()
    for r in references:
        record_id = r['id']
        pdf_exists[record_id] = test_if_pdf_exists(record_id)

    return render_template("pdfs_list.html", references=references, project_id=project_id, pdf_exists=pdf_exists,
                           eligibility_criteria_empty = eligibility_criteria_empty,
                           record_id=record_id, project_name=project_name,  )


def pdf_upload_panel(record_id, project_id):
    sql="SELECT name FROM projects WHERE id=?"
    project_name = sql_select_fetchone(sql, (project_id,))['name']

    sql = f"""
    SELECT id,author1,source, title, pmid,DOI, selection FROM records WHERE id=?
    """
    record_data = sql_select_fetchone(sql, (record_id,))
    return render_template("pdf_upload_panel.html", record_data=record_data, record_id=record_id, project_id=project_id, project_name=project_name,)


def pdf_upload(record_id, project_id, source):

    if 'pdfFile' not in request.files:
        return 'No file uploaded', 400

    file = request.files['pdfFile']
    if file.filename == '':
        return 'No file selected', 400

    try:
        filename = f"r{record_id}.pdf"
        file.save(os.path.join(PDF_UPLOAD_PATH, filename))
        if source == "pass2":
            template = "endpoint_records_screening_pass2_window"
        else:
            template = "endpoint_pdfs_list"
        return redirect(url_for(template, record_id=record_id, project_id=project_id))

    except Exception as e:
        return f'Error processing file: {str(e)}', 500


import os
import re
from utils import *

def extract_NCT(abstract):
    pattern = r'NCT\d{8}'
    match = re.search(pattern, abstract)
    return match.group() if match else ""


def save_reference(project_id, author1, title, abstract, source, nct, pmid, doi, url, database):
    pmid2 = pmid if pmid!="" else "-9"
    doi2 = doi if doi!="" else "@@@"
    sql = "SELECT * FROM records WHERE project=? and (pmid=? OR DOI=?)"
    res = sql_select_fetchone(sql, (project_id, pmid2, doi2))
    if res is not None:
        mssg = f"{title} {source} {pmid} {doi} already exists!"
        return mssg, False

    sql = "INSERT INTO records (project, author1, title, abstract, source, registration_number, pmid, DOI, url, database) VALUES (?,?,?,?,?,?,?,?,?,?)"
    sql_insert_into(sql, (project_id, author1, title, abstract, source, nct, pmid, doi, url, database))

    mssg = f"{title} {source} added"
    return mssg, True

def ZZZsave_reference(project_id, author1, title, abstract, source, nct, pmid, doi, url, database):
    return source, False

def read_endnote_export_file(project_id, database):
    n_added = 0
    n_skipped = 0

    app_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = app_dir + "/tempo/endnote.txt"

    i_author = 1
    title = ""
    i_reference = 0
    with open(file_path, "r", encoding="utf-8") as fichier:
        for ligne in fichier:
            ligne = ligne.strip()
            if ligne=="": continue

            if ligne.startswith("%0 "):
                # new reference
                if i_reference > 0:
                    source = journal+ " " + year+";"+volume+":"+pages
                    nct = extract_NCT(abstract)
                    mssg, added = save_reference(project_id, author1, title, abstract, source, nct, pmid, DOI, url, database)
                    if added:
                        n_added += 1
                    else:
                        n_skipped += 1
                    yield f'data: {mssg}\n\n'

                i_reference += 1
                i_author = 1
                author1 = ""
                title = ""
                year = ""
                abstract = ""
                DOI = ""
                volume = ""
                journal = ""
                pages = ""
                pmid = ""
                url = ""

            if ligne.startswith("%A "):
                if i_author == 1:
                    author1 = ligne[3:]
                i_author += 1

            if ligne.startswith("%T "):
                title = ligne[3:]

            if ligne.startswith("%D "):
                year = ligne[3:]

            if ligne.startswith("%X "):
                abstract = ligne[3:]

            if ligne.startswith("%R "):
                DOI = ligne[3:]

            if ligne.startswith("%V "):
                volume = ligne[3:]

            if ligne.startswith("%B "):
                journal = ligne[3:]

            if ligne.startswith("%P "):
                pages = ligne[3:]

            if ligne.startswith("%M "):
                pmid = ligne[3:]

            if ligne.startswith("%U "):
                url = ligne[3:]

    source = journal + " " + year + ";" + volume + ":" + pages
    nct = extract_NCT(abstract)
    mssg, added = save_reference(project_id, author1, title, abstract, source, nct, pmid, DOI, url, database)
    if added:
        n_added += 1
    else:
        n_skipped += 1
    yield f'data: {mssg}\n\n'

    mssg = f"{i_reference} references screened, {n_added} added, {n_skipped} skipped."
    yield f'data: {mssg}\n\n'

    yield 'data: Stream ended.\n\n'




# file_path = "C:\\Users\\miche\\Downloads\\test endnote export format.txt"
# for reference in read_endnote_export_file(file_path):
#     print(reference["source"])
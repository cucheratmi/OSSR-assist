import os
import re
from utils import *

def extract_NCT(abstract):
    pattern = r'NCT\d{8}'
    match = re.search(pattern, abstract)
    return match.group() if match else ""


def save_reference(project_id, author1, title, abstract, source, nct, pmid, doi, url, acronym, database):
    pmid2 = pmid if pmid!="" else "-9"
    doi2 = doi if doi!="" else "@@@"
    sql = "SELECT * FROM records WHERE project=? and (pmid=? OR DOI=?)"
    res = sql_select_fetchone(sql, (project_id, pmid2, doi2))
    if res is not None:
        mssg = f"{title} {source} {pmid} {doi} already exists!"
        return mssg, False

    sql = "INSERT INTO records (project, author1, title, abstract, source, registration_number, pmid, DOI, url, acronym, database) VALUES (?,?,?,?,?,?,?,?,?,?)"
    sql_insert_into(sql, (project_id, author1, title, abstract, source, nct, pmid, doi, url, acronym, database))

    mssg = f"{title} {source} added"
    print(mssg)
    return mssg, True



########## Endnote #############################

def endnote(project_id):
    database = BIBLIOGRAPHIC_DATABASE["Endnote"]
    n_added = 0
    n_skipped = 0

    app_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = app_dir + "/tempo/ref.txt"

    i_author = 1
    i_reference = 0
    DOI = volume = pages = year = journal = url = author1 = title = abstract = source = nct = acronym = registration_number = pmid = ""
    with open(file_path, "r", encoding="utf-8") as fichier:
        for ligne in fichier:
            ligne = ligne.strip()
            if ligne=="": continue

            if ligne.startswith("%0 "):
                # new reference
                if i_reference > 0:
                    source = journal+ " " + year+"; "+volume+": "+pages
                    nct = extract_NCT(abstract)
                    mssg, added = save_reference(project_id, author1, title, abstract, source, nct, pmid, DOI, url, acronym, database)
                    if added:
                        n_added += 1
                    else:
                        n_skipped += 1

                    mssg = str(i_reference) + ") " + mssg
                    yield f'data: {mssg}\n\n'

                i_reference += 1
                i_author = 1
                DOI = volume = pages = year = journal = url = author1 = title = abstract = source = nct = acronym = pmid =registration_number = ""

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

    source = journal + " " + year + "; " + volume + ": " + pages
    nct = extract_NCT(abstract)
    mssg, added = save_reference(project_id, author1, title, abstract, source, nct, pmid, DOI, url, acronym,  database)
    if added:
        n_added += 1
    else:
        n_skipped += 1

    mssg = str(i_reference) + ") " + mssg
    mssg += ' - last reference'
    yield f'data: {mssg}\n\n'

    mssg = f"{i_reference} references screened, {n_added} added, {n_skipped} skipped."
    yield f'data: {mssg}\n\n'

    yield 'data: Stream ended.\n\n'



############ Pubmed ############################

def pubmed(project_id):
    database = BIBLIOGRAPHIC_DATABASE["Pubmed"]

    n_added = 0
    n_skipped = 0

    app_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = app_dir + "/tempo/ref.txt"

    flagAbstract = False
    flagTitle = False
    flagSource = False
    flagFirstAuthor = True
    DOI = volume = pages = year = journal = url = author1 = title = abstract = source = nct = acronym = pmid = registration_number = ""

    n_records = 0
    with open(file_path, "r", encoding="utf-8") as fichier:
        for line in fichier:
            line = line.strip()
            if line=="": continue

            if flagAbstract:
                if line.startswith('    '):
                    abstract += " " + line.strip()
                else:
                    flagAbstract = False
            if line.startswith('AB  - '):
                abstract = line[6:].strip()
                flagAbstract = True

            if flagTitle:
                if line.startswith('      '):
                    title += " " + line.strip()
                else:
                    flagTitle = False
            if line.startswith('TI  - '):
                title = line[6:].strip()
                flagTitle = True

            if flagSource:
                if line.startswith('      '):
                    source += " " + line.strip()
                else:
                    flagSource = False
            if line.startswith('SO  - '):
                source = line[6:].strip()
                flagSource = True

            if line.startswith('LID - '):
                DOI = line[6:].strip()
                DOI = DOI.replace('[doi]', '').strip()
            if line.startswith('AID - ') and DOI == "":
                DOI = line[6:].strip()
                DOI = DOI.replace('[doi]', '').strip()

            if line.startswith('SI  - '):
                registration_number = line[6:].strip()
                registration_number = registration_number.split('/')[-1].strip()

            if line.startswith('PG  - '):
                pages = line[6:].strip()

            if line.startswith('CN  - '):
                acronym = line[6:].strip()
            if line.startswith('TA  - '):
                journal = line[6:].strip()
            if line.startswith('VI  - '):
                volume = line[6:].strip()
            if line.startswith('DP  - '):
                year = line[6:].strip()
            if line.startswith('AU  - ') and flagFirstAuthor:
                author1 = line[6:].strip()
                flagFirstAuthor = False

            # break
            if line.startswith('PMID'):
                n_records += 1
                if n_records > 1:
                    source = journal + " " + year + "; " + volume + ": " + pages
                    nct = registration_number
                    mssg, added = save_reference(project_id, author1, title, abstract, source, nct, pmid, DOI, url, acronym,  database)
                    if added:
                        n_added += 1
                    else:
                        n_skipped += 1
                    mssg = str(n_records) + ") " + mssg
                    yield f'data: {mssg}\n\n'

                flagAbstract = False
                flagTitle = False
                flagSource = False
                flagFirstAuthor = True
                DOI = volume = pages = year = journal = url = author1 = title = abstract = source = nct = acronym = pmid = registration_number =""

                pmid = line[6:].strip()

    source = journal + " " + year + "; " + volume + ": " + pages
    nct = registration_number
    mssg, added = save_reference(project_id, author1, title, abstract, source, nct, pmid, DOI, url, acronym,  database)
    if added:
        n_added += 1
    else:
        n_skipped += 1
    mssg = str(n_records) + ") " + mssg +" - last reference"
    yield f'data: {mssg}\n\n'

    mssg = f"{n_records} references screened, {n_added} added, {n_skipped} skipped."
    yield f'data: {mssg}\n\n'

    yield 'data: Stream ended.\n\n'


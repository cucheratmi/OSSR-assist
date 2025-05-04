import os
import sqlite3

from utils import *



def add_reference(project_id, DOI, pages, registration_number, acronym, journal, volume, date, author1, title, abstract, source, pmid):

    PUBMED = BIBLIOGRAPHIC_DATABASE['Pubmed']

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()

    # test if reference already exits
    if pmid=="": pmid="-999"
    if DOI=="": DOI = "@@@"
    sql = "SELECT * FROM records WHERE project=? and (pmid=? OR DOI=?)"
    res = cur.execute(sql, (project_id, pmid, DOI))
    r = res.fetchone()
    if r is None:
        source = journal + " " + date + "; " + volume + ":" + pages
        sql = "INSERT INTO records (project, pmid, DOI, registration_number, acronym, author1, title, abstract, source, database) VALUES (?,?,?,?,?,?,?,?,?,?)"
        cur.execute(sql,
                    (project_id, pmid, DOI, registration_number, acronym, author1, title, abstract,source,PUBMED,)
                    )
        con.commit()
    else:
        print("reference already exists!")

    cur.close()
    con.close()


def parse_pubmed_file(content, project_id):
    flagAbstract = False
    abstract = ""
    flagTitle = False
    title = ""
    flagSource = False
    source = ""
    flagFirstAuthor = True
    DOI=volume=pages=date=journal=acronym=registration_number=author1=pmid = ""

    n_records = 0
    for line in content.split('\n'):
        if line=="": continue

        if flagAbstract :
            if line.startswith('    '):
                abstract += " " + line.strip()
            else:
                flagAbstract = False
        if line.startswith('AB  - '):
            abstract = line[6:].strip()
            flagAbstract = True

        if flagTitle :
            if line.startswith('      '):
                title += " " + line.strip()
            else:
                flagTitle = False
        if line.startswith('TI  - '):
            title = line[6:].strip()
            flagTitle = True

        if flagSource :
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
        if line.startswith('AID - ') and DOI=="":
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
            date = line[6:].strip()
        if line.startswith('AU  - ') and flagFirstAuthor:
            author1 = line[6:].strip()
            flagFirstAuthor = False

        # break
        if line.startswith('PMID'):
            n_records += 1
            if n_records>1:
                add_reference(project_id, DOI, pages, registration_number, acronym, journal, volume, date, author1, title, abstract, source, pmid)
                flagAbstract = False
                abstract = ""
                flagTitle = False
                title = ""
                flagSource = False
                source = ""
                flagFirstAuthor = True
                DOI=volume=pages=date=journal=acronym =registration_number=author1=pmid = ""
            pmid = line[6:].strip()

    add_reference(project_id, DOI, pages, registration_number, acronym, journal, volume, date, author1, title, abstract, source, pmid)


# for test

def load_text_file(file_path):
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        raise Exception(f"Error loading file: {str(e)}")

def load_pubmed_file(path):
    if path:
        content = load_text_file(path)
        parse_pubmed_file(content, 1)
    else:
        raise ValueError("File path is not specified")


# path = "C:\\Users\\miche\\Downloads\\pubmed-srai.txt"
# load_pubmed_file(path)

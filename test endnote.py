import os
import re

file_path = "C:\\Users\\miche\\Downloads\\test endnote export format.txt"

def extraire_premier_nct(texte):
    pattern = r'NCT\d{8}'
    match = re.search(pattern, texte)  # search trouve la première occurrence
    return match.group() if match else None


def read_endnote_export_file(file_path):
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
                    nct = extraire_premier_nct(abstract)
                    reference = {'i': i_reference, 'authors1': author1, 'title': title, 'abstract': abstract, 'source': source, 'nct': nct, 'pmid': pmid,
                                 'doi':DOI, 'url': url}
                    yield reference

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

    source = title +  " " + journal+ " " + year+";"+volume+":"+pages
    nct = extraire_premier_nct(abstract)
    reference = {'i': i_reference, 'authors1': author1, 'title': title, 'abstract': abstract, 'source': source, 'nct': nct, 'pmid': pmid,
                 'doi': DOI, 'url': url}
    yield reference


for reference in read_endnote_export_file(file_path):
    print(reference["source"])
from flask import Flask, render_template, request, redirect, url_for, send_file
from utils import *
import pandas as pd

def retraction_watch(project_id):

    sql = "SELECT DOI, pmid, id FROM records WHERE project=?"

    rows = sql_select_fetchall(sql, (1,))
    DOIs = list(set(row['DOI'] for row in rows if row['DOI'] is not None))
    PMIDs = list(set(row['pmid'] for row in rows if row['pmid'] is not None))

    df = load_retraction_watch_dataframe()

    r1 = df[df['OriginalPaperDOI'].str.contains('|'.join(DOIs), case=False, na=False)]
    html1 = "" if r1.empty else r1.to_html()
    print(r1)

    r2 = df[df['OriginalPaperPubMedID'].isin(PMIDs)]
    html2 = "" if r2.empty else r2.to_html()
    print(r2)

    return render_template('retraction_watch.html', project_id=project_id, r1=html1, r2=html2)


def load_retraction_watch_dataframe():
    import requests
    from datetime import datetime
    import io

    # URL de l'API Crossref Labs pour le dataset Retraction Watch
    url = "https://api.labs.crossref.org/data/retractionwatch"

    try:
        # Télécharger les données
        print("Téléchargement des données en cours...")
        response = requests.get(url)
        response.raise_for_status()

        # Charger directement dans un DataFrame
        print("Conversion en DataFrame...")
        df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))

        print(f"DataFrame chargé avec succès. Dimensions : {df.shape}")

        # Afficher les informations sur le DataFrame
        print("\nInformations sur le DataFrame :")
        print(df.info())

        return df

    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement des données : {str(e)}")
        return None
    except pd.errors.EmptyDataError:
        print("Erreur : Le fichier CSV est vide")
        return None
    except Exception as e:
        print(f"Une erreur inattendue s'est produite : {str(e)}")
        return None

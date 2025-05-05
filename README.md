# OSSR - un logiciel open source d'aide à la réalisation des revues systématiques

version 0.1


## Description
Application python d'assistance à la réalisation des revues systématiques. Propose aussi des outils d'IA d'aide 
à la sélection, à l'extraction et à l'évaluation du risque de biais (nécessite un accès à une API payante 
d'un modèle de langage).
Permet la revue systématique des essais cliniques randomisés, des études de technologies diagnostiques 
et aussi d'autres types d'études (hors évaluation du ROB).



## Fonctionnalités
- Importation de références à partir d'un fichier Pubmed, Embase, RIS ou Endnote (format endnote export) 
- Sélection manuelle des références à partir du titre ou de l'abstract
- Suggestion de sélection automatique par IA (nécessite uen clés d'accès à une API à Mistral, ou openai ou anthropic)
- Import des PDFs des références
- Sélection à partir du fulltext (PDF)
- Sélection assistée par un outil d'IA 
- Extraction manuelle des données nécessaires pour la revue systématique (caractéristiques des études, résultats)
- Extraction assistée par un outil d'IA 
- Evaluation du risque de biais avec le ROB2.0 pour les essais cliniques, QUADAS-2 pour les études de technologies diagnostiques
- Evaluation du ROB assisté par un outil d'IA
- Export des résultats de la sélection, de l'extraction, de l'évaluation du risque de biais sous la forme de fichier .CSV ou Excel
- Recherche des références dupliquées par proximité sémantique
- Recherche automatique des publications rétractées (à partir du fichier de Retraction Watch)



## Installation

Soit par clonage, soit en téléchargeant le répertoire compressé (faire ensuite les étapes 2 et 3 à partir 
du répertoire décompressé).   

1) Cloner le dépositoire github
à partir de l’emplacement où vous voulez mettre le répertoire cloné.
```
git clone https://github.com/cucheratmi/OSSR-assist.git
```

2) Créer un environnement virtuel
```
python -m venv ossr-env
source ossr-env/bin/activate  # For Windows: ossr-env\Scripts\activate 
```

3) Installer les dépendances
```
pip install -r requirements.txt
```


4) Configurer les clés d'accès aux API de LLM (optionnel)
Vous pourrez déclarer la clé d'accès à l'API du modèle de langage que vous souhaitez utiliser dans l'application. 
Vous pouvez aussi créer un fichier .env contenant une ou plusieurs clés (cf. le fichier exemple: .env-example.

## Utilisation
Il s'agit d'une application Flask. Une fois le serveur lancer à partir du répertoire de l'application par:

``
python app.py
``

L'application elle-même est accessible avec un navigateur Web (Firefox, Chrome, etc.) à l'adresse http://127.0.0.1:5000
(le navigateur s'ouvre automatique sur certain système).

## Développeurs

- [Michel Cucherat](https://github.com/cucheratmi) 

### Autres contributions 

à venir

## Licence
The OSSR software has an Apache 2.0 [LICENCE](LICENSE). The OSSR team
accepts no responsibility or liability for the use of the OSSR software or any
direct or indirect damages arising out of the application of the tool.



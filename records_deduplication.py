from utils import *
from flask import render_template
import sys
from io import StringIO



def records_deduplication(project_id):

    sql= "SELECT id, title FROM records WHERE project=?"
    rows = sql_select_fetchall(sql, (project_id,))

    corpus = []
    ids = []
    for e in rows:
        id = e["id"]
        ids.append(id)
        title = e["title"]
        corpus.append(title)


    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
    # Initialise an instance of tf-idf Vectorizer
    tfidf_vectorizer = TfidfVectorizer()

    # Generate the tf-idf vectors for the corpus
    tfidf_matrix = tfidf_vectorizer.fit_transform(corpus)

    # compute and print the cosine similarity matrix
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    # print(cosine_sim)

    # We use np.triu_indices to get the upper triangle indices, excluding the diagonal
    indices = np.triu_indices(cosine_sim.shape[0], k=1)
    similarities = cosine_sim[indices]

    # Get the indices of the most similar pairs
    sorted_indices = np.argsort(similarities)[::-1]
    most_similar_pairs = [(indices[0][i], indices[1][i]) for i in sorted_indices]

    most_similar_pairs = [most_similar_pairs[i] for i in range(0, len(most_similar_pairs)) if
                          cosine_sim[most_similar_pairs[i]] > 0.80]

    # Créer un buffer de texte
    buffer = StringIO()
    # Sauvegarder l'ancienne sortie
    ancien_stdout = sys.stdout
    # Rediriger stdout vers le buffer
    sys.stdout = buffer

    print("Most similar pairs (row, column):")
    for pair in most_similar_pairs:
        print(pair, "with similarity", cosine_sim[pair])
        print("  - ", corpus[pair[0]], " (record #", ids[pair[0]], ")")
        print("  - ", corpus[pair[1]], " (record #", ids[pair[1]], ")")
        print("\n")

    # Restaurer stdout
    sys.stdout = ancien_stdout

    # Récupérer le contenu
    output = buffer.getvalue()
    buffer.close()

    print("Contenu capturé:", output)

    return render_template('records_deduplication.html', output=output)
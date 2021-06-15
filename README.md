# SPA Vocabulary

This repo contains scripts for transforming a spreadsheet with controlled vocabularies into RDF and CSV. The CSV is used to render [a simple documentation](https://sapa.github.io/spa-vocabulary/) of the vocabularies.

To get started install the requirements via `pip install -r requirements.txt`

For every update of the vocabulary:

1. Copy the `ControlledTerms.xlsx` (original hosted on SharePoint) into `source`.
2. `python render.py`
3. `python render-csv.py`
4. Commit all changes.

Rendered RDF are found in `target`.
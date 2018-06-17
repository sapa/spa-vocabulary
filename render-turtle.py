# coding: utf-8
import pandas as pd
from rdflib import Graph, Literal, Namespace, URIRef, plugin
from rdflib.serializer import Serializer
from rdflib.namespace import RDF, RDFS, SKOS, OWL
from rdflib.plugins.serializers.nt import NTSerializer


df = pd.read_excel('source/ControlledTerms.xlsx', 'skos')

vocab_ns = Namespace('http://vocab.performing-arts.ch/')

label_columns = []
for ns in ['skos']:
    for p in ['prefLabel', 'altLabel', 'hiddenLabel']:
        for l in ['en', 'de', 'fr', 'it']:
            label_columns.append('skos_' + p + '_' + l)


graph = Graph()
graph.bind('rdfs', RDFS)
graph.bind('skos', SKOS)
graph.bind('owl', OWL)
graph.bind('aat', Namespace('http://vocab.getty.edu/aat/'))
graph.bind('crm', Namespace('http://www.cidoc-crm.org/cidoc-crm/'))
graph.bind('rdabs', Namespace('http://rdaregistry.info/termList/broadcastStand/'))
graph.bind('rdamat', Namespace('http://rdaregistry.info/termList/RDAMaterial/'))
graph.bind('rdacc', Namespace('http://rdaregistry.info/termList/RDAColourContent/'))
graph.bind('rdapm', Namespace('http://rdaregistry.info/termList/RDAproductionMethod/'))
graph.bind('rdavf', Namespace('http://rdaregistry.info/termList/videoFormat/'))
graph.bind('rdagd', Namespace('http://rdaregistry.info/termList/gender/'))
graph.bind('iso639-2', Namespace('http://id.loc.gov/vocabulary/iso639-2/'))
graph.bind('spav', vocab_ns)

uris = []

scheme = None
for idx, row in df.iterrows():
    uri = None
    # new scheme?
    if not pd.isnull(row['skos_ConceptScheme']):
        # save old graph first?
        scheme = row['skos_ConceptScheme'].strip()
        scheme_uri = uri = URIRef(vocab_ns[scheme])
        try:
            assert uri not in uris
        except AssertionError:
            print(f'{uri} already exists!')
        uris.append(uri)
        graph.add((scheme_uri, RDF.type, SKOS.ConceptScheme))
        # TODO: Validate if this is always correct.
        graph.add((scheme_uri, RDF.type, URIRef('http://www.cidoc-crm.org/cidoc-crm/E55_Type')))
        scheme_ns = Namespace(scheme_uri + '/')
    # concept
    elif not pd.isnull(row['skos_Concept']) and scheme_ns:
        # uri = URIRef(scheme_ns[row['skos_Concept'].strip()])
        uri = URIRef(vocab_ns[f'{scheme}-{row["skos_Concept"].strip()}'])
        try:
            assert uri not in uris
        except AssertionError:
            print(f'{uri} already exists!')
        uris.append(uri)
        graph.add((uri, RDF.type, SKOS.Concept))
        graph.add((uri, SKOS.inScheme, scheme_uri))
        # broader, narrower
        if not pd.isnull(row['broader']):
            if row['broader'].strip() == '-':
                graph.add((uri, SKOS.topConceptOf, scheme_uri))
                graph.add((scheme_uri, SKOS.hasTopConcept, uri))
            else:
                # broader_uri = URIRef(scheme_ns[row['broader'].strip()])
                broader_uri = URIRef(vocab_ns[f'{scheme}-{row["broader"].strip()}'])
                graph.add((uri, SKOS.broader, broader_uri))
                graph.add((broader_uri, SKOS.narrower, uri))
    # concepts and schemes
    if not pd.isnull(row['rdfs_comment_en']):
        graph.add((uri, RDFS.comment, Literal(
            row['rdfs_comment_en'].strip(), lang='en')))
    for c in label_columns:
        if c in row and not pd.isnull(row[c]) and row[c].strip() != '-':
            ns, pred, lang = c.split('_')
            for s in row[c].split(';'):
                graph.add((uri, SKOS[pred], Literal(s.strip(), lang=lang)))
    # same as
    if not pd.isnull(row['skos_exactMatch']) and row['skos_exactMatch'].strip() != '-':
        for s in row['skos_exactMatch'].split(';'):
            graph.add((uri, SKOS.exactMatch, URIRef(s.strip())))

with open('target/vocabulary.ttl', 'wb') as f:
    f.write(graph.serialize(format='turtle'))

# coding: utf-8
import pandas as pd
from rdflib import Graph, Dataset, Literal, Namespace, URIRef, plugin
from rdflib.serializer import Serializer
from rdflib.namespace import RDF, RDFS, SKOS, OWL, XSD
from rdflib.plugins.serializers.nt import NTSerializer
import datetime
import pytz


vocab_ns = Namespace('http://vocab.performing-arts.ch/')

label_columns = []
for ns in ['skos']:
    for p in ['prefLabel', 'altLabel', 'hiddenLabel']:
        for l in ['en', 'de', 'fr', 'it']:
            label_columns.append('skos_' + p + '_' + l)
label_columns.append('skos_definition_en')

vocabs = dict()
vocabs['prov'] = Namespace('http://www.w3.org/ns/prov#')
vocabs['ldp'] = Namespace('http://www.w3.org/ns/ldp#')
vocabs['aat'] = Namespace('http://vocab.getty.edu/aat/')
vocabs['crm'] = Namespace('http://www.cidoc-crm.org/cidoc-crm/')
vocabs['rdabs'] = Namespace('http://rdaregistry.info/termList/broadcastStand/')
vocabs['rdamat'] = Namespace('http://rdaregistry.info/termList/RDAMaterial/')
vocabs['rdacc'] = Namespace('http://rdaregistry.info/termList/RDAColourContent/')
vocabs['rdapm'] = Namespace('http://rdaregistry.info/termList/RDAproductionMethod/')
vocabs['rdavf'] = Namespace('http://rdaregistry.info/termList/videoFormat/')
vocabs['rdagd'] = Namespace('http://rdaregistry.info/termList/gender/')
vocabs['iso639-2'] = Namespace('http://id.loc.gov/vocabulary/iso639-2/')
vocabs['wd'] = Namespace('http://www.wikidata.org/entity/')
vocabs['gnd'] = Namespace('http://d-nb.info/gnd/')
vocabs['rico'] = Namespace('https://www.ica.org/standards/RiC/ontology#')
vocabs['ric-rst'] = Namespace('https://www.ica.org/standards/RiC/vocabularies/recordSetTypes#')
vocabs['ebucore'] = Namespace('https://www.ebu.ch/metadata/ontologies/ebucore#')
vocabs['eclap'] = Namespace('http://www.eclap.eu/schema/eclap/')
vocabs['dct'] = Namespace('http://purl.org/dc/terms/')
vocabs['premis'] = Namespace('http://www.loc.gov/premis/rdf/v1#')


ds = Dataset()
graph = ds.graph(URIRef('http://vocab.performing-arts.ch/container/context'))
graph.bind('rdfs', RDFS)
graph.bind('skos', SKOS)
graph.bind('owl', OWL)
graph.bind('spav', vocab_ns)
for k, v in vocabs.items():
    graph.bind(k, v)

ldp = URIRef('http://vocab.performing-arts.ch/container')
graph.add((ldp, RDF.type, vocabs['prov'].Entity))
graph.add((ldp, RDF.type, vocabs['ldp'].Resource))
graph.add((ldp, vocabs['prov'].generatedAtTime, Literal(
    datetime.datetime.now(pytz.timezone('Europe/Zurich')).isoformat(), datatype=XSD.dateTime)))

uris = []

for sheet in ['skos', 'formats']:
    df = pd.read_excel('source/ControlledTerms.xlsx', sheet, dtype=str, engine='openpyxl')

    scheme = None
    for idx, row in df.iterrows():
        uri = None
        rico = False
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
            scheme_ns = Namespace(scheme_uri + '/')
        # concept
        elif not pd.isnull(row['skos_Concept']) and scheme_ns:
            uri = URIRef(vocab_ns[f'{scheme}{row["skos_Concept"].strip()}'])
            try:
                assert uri not in uris
            except AssertionError:
                print(f'{uri} already exists!')
            uris.append(uri)
            graph.add((uri, RDF.type, SKOS.Concept))
            if not pd.isnull(row['additional_class']):
                for c in row['additional_class'].split(';'):
                    p = c.strip().split(':')[0]
                    q = c.strip().split(':')[1]
                    if p in vocabs:
                        graph.add((uri, RDF.type, URIRef(vocabs[p] + q)))
                        if p == 'rico':
                            rico = True
            if not rico and sheet == 'skos':
                graph.add((uri, RDF.type, URIRef('http://www.cidoc-crm.org/cidoc-crm/E55_Type')))

            graph.add((uri, SKOS.inScheme, scheme_uri))
            # broader, narrower
            if not pd.isnull(row['broader']):
                if row['broader'].strip() == '-':
                    graph.add((uri, SKOS.topConceptOf, scheme_uri))
                    graph.add((scheme_uri, SKOS.hasTopConcept, uri))
                else:
                    # broader_uri = URIRef(scheme_ns[row['broader'].strip()])
                    broader_uri = URIRef(vocab_ns[f'{scheme}{row["broader"].strip()}'])
                    graph.add((uri, SKOS.broader, broader_uri))
                    graph.add((broader_uri, SKOS.narrower, uri))
        # concepts and schemes
        if not pd.isnull(row['rdfs_comment_en']):
            graph.add((uri, RDFS.comment, Literal(
                row['rdfs_comment_en'].strip(), lang='en')))
        for c in label_columns:
            if c in row and not pd.isnull(row[c]) and row[c].strip() != '-':
                ns, pred, lang = c.split('_')
                if not pd.isnull(row[c]):
                    for s in row[c].split(';'):
                        graph.add((uri, SKOS[pred], Literal(s.strip("' "), lang=lang)))
                        if rico and pred == 'prefLabel':
                            graph.add((uri, URIRef('https://www.ica.org/standards/RiC/ontology#name'), Literal(s.strip("' "), lang=lang)))
        # same as
        if not pd.isnull(row['skos_exactMatch']) and row['skos_exactMatch'].strip() != '-':
            for s in row['skos_exactMatch'].split(';'):
                s = s.strip()
                if s[:4] == 'http':
                    graph.add((uri, SKOS.exactMatch, URIRef(s)))
                elif len(s.split(':'))==2:
                    p = s.split(':')[0]
                    q = s.split(':')[1]
                    if p in vocabs:
                        graph.add((uri, SKOS.exactMatch, URIRef(vocabs[p] + q)))
        # format extras
        if sheet == 'formats':
            if not pd.isnull(row['premis_formatVersion']) and row['premis_formatVersion'].strip() != '':
                graph.add((uri, URIRef(f'{vocabs["premis"]}formatVersion'), Literal(row['premis_formatVersion'].strip())))
            if not pd.isnull(row['ebucore_hasMimeType']) and row['ebucore_hasMimeType'].strip() != '':
                graph.add((uri, URIRef(f'{vocabs["ebucore"]}hasMimeType'), Literal(row['ebucore_hasMimeType'].strip())))


with open('target/vocabulary.ttl', 'w') as f:
    f.write(graph.serialize(format='turtle'))

with open('target/vocabulary.nq', 'w') as f:
    f.write(ds.serialize(format='nquads'))
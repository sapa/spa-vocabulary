# coding: utf-8
import pandas as pd


df = pd.read_excel('source/ControlledTerms.xlsx', 'skos')

df.dropna(how='all', inplace=True)
df['context'].fillna(method='ffill', inplace=True)
df['scheme'] = ~df['skos_ConceptScheme'].isnull()

# TODO: write index as order number for later sorting

# merge ConceptScheme and Concept to URI
df['skos_ConceptScheme'].fillna(method='ffill', inplace=True)
df['skos_Concept'].fillna('', inplace=True)
# df['skos_Concept'] = df['skos_Concept'].apply(lambda x: int(bool(x)) * '-' + x)
df['id'] = 'http://vocab.performing-arts.ch/' + \
    df['skos_ConceptScheme'].str.strip() + df['skos_Concept'].str.strip()
df['broader'].fillna('', inplace=True)
df['broader'].replace('-', '', inplace=True)
# df['broader'] = df['broader'].apply(lambda x: int(bool(x)) * '-' + x)
df['parent'] = df.apply(lambda x: '' if x['scheme'] else 'http://vocab.performing-arts.ch/' +
                        x['skos_ConceptScheme'].strip() + x['broader'].strip(), axis=1)
df['skos_exactMatch'].replace('-', '', inplace=True)
df['skos_exactMatch'].replace(' ', '', inplace=True)
df.drop(['skos_ConceptScheme', 'skos_Concept', 'broader'], axis=1, inplace=True)

df = df[['id', 'parent', 'scheme', 'context', 'domain', 'property', 'skos_exactMatch', 'rdfs_comment_en', 'skos_prefLabel_en', 'skos_altLabel_en',
         'skos_hiddenLabel_en', 'skos_prefLabel_de', 'skos_altLabel_de', 'skos_prefLabel_fr', 'skos_altLabel_fr', 'skos_prefLabel_it', 'skos_altLabel_it', 
         'skos_definition_en']]

df.index.name = 'sort'
df.to_csv('docs/vocabulary.csv', index=True, header=True)

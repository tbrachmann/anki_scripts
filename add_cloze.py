from vocab_df import make_vocab_df
from db import AnkiDb
import re
from sqlalchemy.sql import *
import pandas as pd
import numpy as np
import platform
import MeCab
from jnlp import *

if "Microsoft" in platform.platform():
    v1_URI = "/mnt/c/Users/Tobias/AppData/Roaming/Anki2/v1 test/collection.anki2"
else:
    v1_URI = "/home/tobiasrb/.local/share/Anki2/v1 test/collection.anki2"

# the goal is to go through the entire collection
# and see what cards I have and which ones I'm missing

db = AnkiDb(v1_URI)

conn = db.engine.connect()
notes = pd.read_sql(str(select([db.get_table('notes')])), db.engine)
models = dict(db.fields_by_id)

def notes_and_field_names(x):
    notes = [y.strip() for y in x['flds'].split("\u001f")]\
            + [x['id']]
    model_id = str(x['mid'])
    model_names = [x['name'] for x in models[model_id]]\
                  + ['nid']
    return {name: field for name, field in zip(model_names, notes)}

notes_and_fields = notes.apply(notes_and_field_names, axis=1)
notes_and_fields_eav = pd.DataFrame(list(notes_and_fields))
df = notes_and_fields_eav.melt(id_vars=['nid'],
                               var_name='field',
                               value_name='value')\
                         .dropna(subset=['value'])

# go through the n3_vocab and iter
# where n3_vocab value is in the kanji field of notes, put the note id there
# this is a groupby!
def match_kanji(x, vocab, vocab_col):
    kanji = x.values[0][0]
    matches = []
    for row in vocab.itertuples():
        if kanji in getattr(row, vocab_col):
            matches.append(row.nid)
    matches = pd.DataFrame({'nid' : matches})
    matches['Kanji'] = [kanji] * len(matches)
    return matches        

# only add cloze to kanji odyssey note type, so needs df_filtered
example_col = "Example Sentence"
ko_notes = notes_and_fields_eav.loc[pd.notna(notes_and_fields_eav[example_col])]
ko_notes = ko_notes.dropna(axis=1, how='all')
ko_notes = ko_notes.replace('', np.nan)

# see how many there are where you can identify the vocab word in the example sentence
# for exactly half I can find the vocab word in the example sentence easily
# for the half that I can't immediately find them: 1308
#   * 1058 don't have example sentences
#   * 250 remaining that are the problem

clozify = ko_notes[pd.notna(ko_notes['Example Sentence'])]

# what to do? maybe use pattern to find the lemma
# lemma - the dictionary form of the word (many different conjugations have the same lemma)
# tokenize -> lemmatize -> add cloze -> join string
t = MeCab.Tagger()
def parse(sentence):
    m = t.parse(sentence)
    return [{x.split("\t")[0] : x.split("\t")[1].split(",")}
            for x in m.split("\n") if x != 'EOS' and x != '']

clozify_dict = [x for x in clozify['Example Sentence'].apply(lambda x: parse(x))]
# before issuing the update statments, need to replace nan with ''

sentence = clozify.iloc[0]['Example Sentence']

from vocab_df import make_vocab_df
from db import AnkiDb
import re
from sqlalchemy.sql import *
import pandas as pd

url = "http://www.tanos.co.uk/jlpt/jlpt3/vocab/"

# the goal is to go through the entire collection
# and see what cards I have and which ones I'm missing

db = AnkiDb()

n3_vocab = make_vocab_df(url)

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

# matched_vocab = n3_vocab.groupby('Kanji').apply(
#     lambda x: match_kanji(x, df, 'value')
# )

df_filtered = df.loc[~df.field.str.contains("Example")]

final = []
for row in n3_vocab.itertuples():
    kanji = row.Kanji
    if pd.isna(kanji):
        continue
    hiragana = row.Hiragana
    matches = []
    for vocab_row in df_filtered.itertuples():
        if kanji in vocab_row.value:
            matches.append(vocab_row.nid)
    matches = pd.DataFrame({'nid' : matches})
    matches['Kanji'] = [kanji] * len(matches)
    final.append(matches)
final = pd.concat(final)

matched_on_kanji = final.merge(df_filtered)

n3_kanji = set(make_vocab_df(url).Kanji.unique())
missing = n3_kanji - set(matched_on_kanji.Kanji.unique())
    
# now for each vocab word
# go through all rows

# # gotta match each value with all vcab
# def match_field(x, vocab):
#     return any((y in x for y in vocab))

# unique_kanji = set(n3_vocab.loc[pd.notna(n3_vocab["Kanji"]),
#                                 ["Kanji"]])

# matched_kanji = df.value.apply(
#     lambda x: match_field(x, unique_kanji)
# )

# ok we can match like this, but how do we get the n3 vocab thats missing                                                      

# zip fields and note values

# now I need to get a comprehensive list of my notes
# get the kanji field of all the possible card types
# Filtered Deck 1 is RTK kanji cards
# Filtered Deck 2 is 2001 Kanji reading cards
# Kanji odyssey vocab has no cards
# J1B Tangou has some kanji but not much
# J1B Kanji has kanji on the back
# Are these the same card types? Yes - Japanese vocab cards
# Vocab kanji practice has a whole lot of kanji cards
# Nihongo no tangou main deck has reading/writing cards

# hiragana/kanji -> easy to deal with because you know the fields
# japanese vocab has reading/writing/kanji
# 2001 a kanji odyssey has reading/kanji
# harder to deal with (both basic note type)
# j1b kanji is guaranteed to have SOME kanji on the back
# j1b tango is not
# basic (and reversed card) is the RTK deck before I got fancy with the size
# of the character (could also migrate all of these to the fanlcier kanji cards as well)

# now I just need to do some parsing...
# split the deck up into kanji | hiragana

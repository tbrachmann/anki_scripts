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

KANJI_START = int("4e00", 16)
KANJI_END = int("9faf", 16)

kanji = {chr(x) for x in range(KANJI_START, KANJI_END+1)}
only_chars = re.compile("[\w^\d^-]")
only_english = re.compile("[a-zA-Z\W]*")
only_japanese = re.compile("[^a-z^A-Z\W]*")

def contains_kanji(x):
    chars = only_chars.findall(x)
    return all((char in kanji for char in chars))

def is_english(x):
    return only_english.fullmatch(x) != None

conn = db.engine.connect()
notes = pd.read_sql(str(select([db.get_table('notes')])), db.engine)
models = dict(db.fields_by_id)

def notes_and_field_names(x):
    notes = x['flds'].split("\u001f")
    model_id = str(x['mid'])
    model_names = [x['name'] for x in models[model_id]]
    return {name: field for name, field in zip(model_names, notes)}

notes_and_fields = notes.apply(notes_and_field_names, axis=1)

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

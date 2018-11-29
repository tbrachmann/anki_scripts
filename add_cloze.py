from vocab_df import make_vocab_df
from part_of_speech import *
from db import AnkiDb
import re
from sqlalchemy.sql import *
import pandas as pd
import numpy as np
import platform
import MeCab
from jnlp import *
import os
from utils import is_english

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

clozify_dicts = clozify.apply(lambda x: dict(x), axis=1).tolist()
# make this better, no more dict, use tuple instead
# can i serialize this output? put python list in CSV
def tokenize_all(clozify_dicts):
    for note in clozify_dicts:
        note['tokens'] = tokenize(note['Example Sentence'])
        # before issuing the update statments, need to replace nan with ''
    return clozify_dicts

html_tag = re.compile('<[a-z/]*>')
commas = re.compile(chr(int('3001', 16)))
dot = re.compile(chr(int('30FB', 16)))
# no support for \P in re
# surround by non-word, non-space character?
punctuation_surround = re.compile('\W[\w\s]*\W')
numbers = re.compile("[一二三四五六七八九十]")

def sanitize(x):
    x = re.sub(html_tag, '', x)
    x = re.sub(commas, '', x)
    x = re.sub(dot, '', x)
    x = re.sub(punctuation_surround, '', x)
    x = re.sub(numbers, '', x)
    return x

pickle_file = 'clozify_output.pkl'
if os.path.isfile(pickle_file):
    clozify_output = pd.read_pickle(pickle_file)
else:
    clozify_output = pd.DataFrame(tokenize_all(clozify_dicts))
    # strip stuff
    clozify_output['word'] = clozify_output['Vocab Word (with Kanji)']\
                             .apply(sanitize)
    clozify_output['word_token'] = clozify_output.word.apply(tokenize)
    clozify_output['part_of_speech'] = clozify_output.word_token.apply(get_pos)
    clozify_output.to_pickle(pickle_file)

# thoughts
# what about phrases like kinisuru? tokenized into 3 different tokens
# what about noun/suru verbs?
# should i tokenize vocab word also?
# def is_multipart_verb

def cloze(word):
    return '[]'

def clozify(note):
    word = [x['token'] for x in note['word_token']]
    tokens = note['tokens']
    word_tokens = note['word_token']
    pos = note['part_of_speech']
    new_list = []
    if pos == 'Phrase':
        len_word = len(word_tokens)
        lemmas = {x['lemma'] for x in word_tokens}
        i = 0
        j = i+len_word
        new_list = [None] * len(tokens)
        while j <= len(tokens):
            test_lems = {x['lemma'] for x in tokens[i:j]}
            if test_lems == lemmas:
                new_list[i] = cloze(tokens[i]['token']).replace("}}", "")
                for x in range(i+1, j-1):
                    new_list[x] = tokens[x]['token']
                new_list[j-1] = cloze(tokens[j-1]['token']).replace("{{c1:", "")
                i = j
                j = i+len_word
            else:
                for x in range(i, j):
                    new_list[x] = tokens[x]['token']
                i += 1
                j += 1
        while i < len(tokens):
            new_list[i] = tokens[i]['token']
            i += 1
    elif pos == 'Verb' or pos == 'Adjective':
        for dict in tokens:
            token = dict['token']
            lemma = dict['lemma']
            if lemma in word:
                new_list += [cloze(token)]
            else:
                new_list += [token]
    # noun and adverb
    else:
        for dict in tokens:
            token = dict['token']
            lemma = dict['lemma']
            if any([x in lemma for x in word]):
                new_list += [cloze(token)]
            else:
                new_list += [token]
    new_sentence = ''
    for token in new_list:
        if is_english(token):
            new_sentence += token + " "
        else:yyyyyyyyyyyyyyyyy
            new_sentence += token
    return new_sentence

new_sentence_pickle = 'clozify_sentence.pkl'
# how to do this correctly? needs to look ahead a little...
clozify_output['new_sentence'] = clozify_output.apply(clozify ,axis=1)

clozify_output.to_csv('clozify_sentence.tsv', sep='\t')
problems = clozify_output[~clozify_output['new_sentence'].str.contains('}}')]
problems.to_csv('problems.tsv', sep='\t')
clozify_output.to_pickle(new_sentence_pickle)

notes = db.get_table('notes')
def make_stmnt(x):
    flds = [x['Vocab Word (with Kanji)'],
            x['Reading'],
            x['Meaning'],
            x['Example Sentence'],
            x['new_sentence']]
    flds = "\u001f".join(flds)
    stmnt = notes.update()\
                 .where(notes.c.id == int(x['nid']))\
                 .values(flds = flds)
    conn.execute(stmnt)
clozify_output = clozify_output.replace(np.nan, "")    
clozify_output.apply(make_stmnt, axis=1)
db.engine.dispose()

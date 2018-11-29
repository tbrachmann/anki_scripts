def is_phrase(tokens):
    parts_of_speech = {token['part_of_speech'] for token in tokens}
    allowed = {'Verb', 'Adjective', 'Noun'}
    # at least 2 in there
    verb_combo = len(allowed & parts_of_speech) >= 2
    particle_included = parts_of_speech >= allowed
    return verb_combo or particle_included
    

def is_verb(tokens):
    return tokens[-1]['part_of_speech'] == 'Verb' \
        or tokens[-1]['part_of_speech'] == 'Determiner'

def is_adverb(tokens):
    return {x['part_of_speech'] for x in tokens} >= {'Adverb'}

def is_noun(tokens):
    return all(["Noun" in x['part_of_speech'] for x in tokens])

def is_adjective(tokens):
    return all(["Adjective" in x['part_of_speech'] for x in tokens])

def get_pos(tokens):
    if len({x['token'] for x in tokens}) == 1:
        tokens = [tokens[0]]
    if len(tokens) == 2 and tokens[1]['token'] == chr(int('3005', 16)):
        tokens = [tokens[0]]*2
    tokens = [x for x in tokens if x['part_of_speech'] != 'Prefix']
    if len(tokens) == 0:
        return "Noun"
    if is_phrase(tokens):
        return "Phrase"
    if is_adverb(tokens):
        return "Adverb"
    if is_noun(tokens):
        return "Noun"
    if is_adjective(tokens):
        return "Adjective"
    else:
        return "Verb"

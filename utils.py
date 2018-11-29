import re

KANJI_START = int("4e00", 16)
KANJI_END = int("9faf", 16)
HIRAGANA_START = int("3040", 16)
HIRAGANA_END = int("309f", 16)
KATAKANA_START = int("30a0", 16)
KATAKANA_END = int("30ff", 16)

kanji = {chr(x) for x in range(KANJI_START, KANJI_END+1)}
hiragana = {chr(x) for x in range(HIRAGANA_START, HIRAGANA_END+1)}
katakana = {chr(x) for x in range(KATAKANA_START, KATAKANA_END+1)}
kana = hiragana | katakana
only_chars = re.compile("[\w^\d^-]")
only_english = re.compile("[a-zA-Z]*")
only_japanese = re.compile("[^a-z^A-Z\W]*")

def contains_kanji(x):
    chars = only_chars.findall(x)
    return any((char in kanji for char in chars))

def is_english(x):
    return only_english.fullmatch(x) != None

def only_kana(x):
    chars = only_chars.findall(x)
    return all((char in kana for char in chars))

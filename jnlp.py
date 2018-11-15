import lxml.html as l
import requests
from utils import is_english
import os
import subprocess

base = "https://jisho.org"
search_url = os.path.join(base, "search")
# better to parse using the ruby wrapper
# write ruby scripts and then call them with subprocess
def tokenize(sentence):
    proc = subprocess.run(['ruby', 'jnlp.rb', sentence], encoding='utf=8',
                          stdout=subprocess.PIPE)
    output = proc.stdout
    tokens, lemmas = proc.stdout.split("TOKENS")[1].split("LEMMAS")
    tokens = tokens.strip().split("\n")
    lemmas = lemmas.strip().split("\n")
    # # token
    # # lemma
    return [{x[0] : x[1]} for x in zip(tokens, lemmas)]

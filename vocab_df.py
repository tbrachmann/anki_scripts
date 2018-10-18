import requests
import lxml.html as l
import sys
import pandas as pd
import numpy as np

def make_vocab_df(url):

    content = l.parse(url)
    tables = content.getroot().cssselect('table')
    vocab_table = max(tables, key=lambda x: len(x))
    headers = [x.text for x in vocab_table[0]]

    def martial_row(row):
        cells = [link.text for cell in row
                 for link in cell]
        if len(cells) < 3:
            kanji = [np.nan]
            cells = kanji + cells
        return dict([x for x in zip(headers, cells)])

    rows = [martial_row(row) for row in vocab_table[1:]]
    df = pd.DataFrame(rows, columns=headers)
    
    return df

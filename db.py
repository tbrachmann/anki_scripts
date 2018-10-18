import sqlalchemy as sqla
from sqlalchemy.orm import sessionmaker, Session
import sqlalchemy.sql as sql
import json
import platform

if "Microsoft" in platform.platform():
    URI = "/mnt/c/Users/Tobias/AppData/Roaming/Anki2/User 1/collection.anki2"
else:
    URI = "/home/tobiasrb/.local/share/Anki2/User 1/collection.anki2"

class AnkiDb:

    def __init__(self, url=URI):
        self.engine = sqla.create_engine("sqlite:///" + URI)
        self.meta = sqla.MetaData()
        self.meta.reflect(bind=self.engine)

    def _get_col_attr(self, attr):
        col = self.meta.tables['col']
        conn = self.engine.connect()
        result = conn.execute(sql.select([col])).fetchone()
        result = getattr(result, attr)
        return json.loads(result)

    def get_table(self, name):
        return self.meta.tables[name]
    
    @property
    def decks(self):
        decks = self._get_col_attr("decks")
        return {id: decks[id]['name'] for id in decks}

    @property
    def models(self):
        models = self._get_col_attr("models")
        return models

    @property
    def fields_by_name(self):
        models = dict(self.models)
        return {models[x]['name'] : models[x]['flds']
                for x in models}

    @property
    def fields_by_id(self):
        models = dict(self.models)
        return {x : models[x]['flds']
                for x in models}

    # we need to match note types with models
    # one table for each note type?
    # or EAV style
    # kanji, hiragana, note id,
    # for note type

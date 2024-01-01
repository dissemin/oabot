# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import sessionmaker
from oabot.dbconfig import get_engine
import requests

Base = declarative_base()
def get_session():
     return sessionmaker(bind=get_engine())

"""
These user-stats can be synchronized with Wikipedia with the following SQL query on the replicas:

SELECT COUNT(1) AS nb_edits, revision.rev_user_text
FROM change_tag INNER JOIN revision ON change_tag.ct_rev_id = revision.rev_id
WHERE change_tag.ct_tag = "OAuth CID: 817"
GROUP BY revision.rev_user_text
ORDER BY nb_edits;

To connect to the enwiki replica:
mariadb --defaults-file=$HOME/replica.my.cnf -h enwiki.analytics.db.svc.wikimedia.cloud enwiki_p

"""

class UserStats(Base):
    """
    Database record which holds the number of user edits
    """
    __tablename__ = 'userstats'
    id = Column(Integer, primary_key=True, autoincrement=True)
    wiki = Column(String(32))
    user_name = Column(String(128))
    nb_edits = Column(Integer)
    nb_links = Column(Integer)

    def __repr__(self):
        return "<UserStats for %s: %d,%d>" % (self.user_name, self.nb_edits, self.nb_links)

    @classmethod
    def increment_user(cls, wiki, user_name, edits, links):
        session = get_session()()

        instance = session.query(cls).filter_by(wiki=wiki, user_name=user_name).first()
        if not instance:
            instance = cls(wiki=wiki, user_name=user_name, nb_edits=0, nb_links=0)
            session.add(instance)

        instance.nb_edits += edits
        instance.nb_links += links
        session.commit()
        session.close()


    @classmethod
    def get_leaderboard(cls):
        session = get_session()()
        stats = session.query(cls).filter(cls.nb_edits != 0).order_by(cls.nb_edits)
        session.close()
        return reversed(list(stats))

    @classmethod
    def sync_from_wikipedia(cls, wiki, dct):
        session = get_session()()
        for user, value in list(dct.items()):
            instance = session.query(cls).filter_by(wiki=wiki, user_name=user).first()
            if not instance:
                instance = cls(wiki=wiki, user_name=user, nb_edits=value, nb_links=value)
                session.add(instance)
            else:
                instance.nb_edits = value
                instance.nb_links = value
        session.commit()
        session.close()

    @classmethod
    def get(cls, wiki, user):
        session = get_session()()
        instance = session.query(cls).filter_by(wiki=wiki, user_name=user).first()
        if not instance:
            instance = cls(wiki=wiki, user_name=user, nb_edits=0, nb_links=0)
        session.close()
        return instance

    def unicode_name(self):
        if type(self.user_name) == str:
            try:
                return self.user_name.decode('ascii')
            except (UnicodeDecodeError, AttributeError) as e:
                return self.user_name
        else:
            return self.user_name

if __name__ == '__main__':

    engine = get_engine()

    Base.metadata.create_all(engine)
    dct = {
    'Zuphilip': 1,
    'Stefan Weil': 1,
    'Ocaasi': 1,
    'Saung Tadashi': 1,
    'Slaporte': 1,
    'MartinPoulter': 1,
    'Shizhao': 1,
    'Samwalton9': 2,
    'DatGuy': 2,
    'Aarontay': 2,
    'Jakob.scholbach': 3,
    'Harej': 3,
    'HenriqueCrang': 3,
    'Gamaliel': 3,
    'Headbomb': 5,
    'CristianCantoro': 5,
    'Sadads': 10,
    'Waldir': 11,
    'Jarble': 11,
    'Josve05a': 12,
    'Nihlus Kryik': 19,
    'Pintoch': 25,
    'A3nm': 38,
    'Lauren maggio': 40,
    'Nemo bis': 241,
    }
    UserStats.sync_from_wikipedia('en', dct)
    for user in UserStats.get_leaderboard():
        print(user)

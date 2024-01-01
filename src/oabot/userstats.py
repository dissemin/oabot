# -*- coding: utf-8 -*-

import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Sequence
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text
from oabot.dbconfig import *
import requests

Base = declarative_base()
def get_session():
     return sessionmaker(bind=get_engine())

"""
These user-stats can be synchronized with Wikipedia with the following SQL query on the replicas.

To connect to the enwiki replica:
mariadb --defaults-file=$HOME/replica.my.cnf -h enwiki.analytics.db.svc.wikimedia.cloud enwiki_p

Feed the output of the function to UserStats.sync_from_wikipedia() if the connection to the replica is set.

"""

replica_stats_query_sql = """SELECT COUNT(r.rev_id) AS nb_edits, u.user_name as user_name
FROM change_tag ct
INNER JOIN revision r
ON ct.ct_rev_id = r.rev_id
JOIN change_tag_def ctd
ON ctd.ctd_id = ct.ct_tag_id
AND ( ctd.ctd_name = "OAuth CID: 817"
OR ctd.ctd_name = "OAuth CID: 1779" )
JOIN actor a
ON a.actor_id = r.rev_actor
JOIN user u
ON u.user_id = a.actor_user
GROUP BY r.rev_actor
ORDER BY nb_edits;"""

def get_stats_from_replica():
    replica = get_engine_replica()
    with e.connect() as conn:
        s = text(replica_stats_query_sql).columns("nb_edits", "user_name")
        rs = conn.execute()
        dct = {row.user_name.decode("utf8"): row.nb_edits for row in rs}

    return dct

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
    # dct = get_stats_from_replica()
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

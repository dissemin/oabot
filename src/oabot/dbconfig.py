# -*- coding: utf-8 -*-

from sqlalchemy import create_engine

_config = None
_url = 'sqlite:///:memory:'


def get_engine():
    engine = create_engine(_url, echo=False)
    return engine

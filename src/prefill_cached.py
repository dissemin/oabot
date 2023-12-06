#!/usr/bin/python3
# -*- coding: utf-8  -*-
""" Script to fetch additional Dissemin data for cached suggestions """
#
# (C) CAPSH, 2023
#
# Distributed under the terms of the MIT license.
#

from app import get_proposed_edits, app
import os

for page in os.listdir("cache"):
    if page.endswith("json"):
        title = page.replace(".json", "").replace("#", "/")
        print(title)
        get_proposed_edits(title, True, True, False)
# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

from settings import *
import subprocess32 as subprocess
import tempfile
import shutil
import os
import requests
import PyPDF2
from PyPDF2.utils import PyPdfError
from StringIO import StringIO

class RunnableError(Exception):
    pass


class AcademicPaperFilter(object):
   def classify_url(self, url):
        """
        Download a potential PDF file at a given URL and
        check if it looks like a legitimate scholarly paper.
        """
        try:
            r = requests.get(url, headers={'User-Agent':
                    OABOT_USER_AGENT}, verify=False)
            return self.check_nb_pages(r.content)
        except requests.exceptions.RequestException as e:
            print e
            return False

   def check_nb_pages(self, data):
        """
        Does this PDF contain enough pages?
        """
        try:
            s_io = StringIO(data)
            reader = PyPDF2.PdfFileReader(s_io)
            num_pages = reader.getNumPages()
            print("num pages: %d" % num_pages)
            return num_pages > 2
        except PyPdfError as e:
            return False



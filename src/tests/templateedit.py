# -*- encoding: utf-8 -*-
from __future__ import unicode_literals

import unittest

from oabot.main import *

class TemplateEditTests(unittest.TestCase):

    def propose_change(self, text, page_name='Test page', only_doi=False):
        wikicode = mwparserfromhell.parse(text)
        for template in wikicode.filter_templates():
            edit = TemplateEdit(template, page_name)
            edit.propose_change(only_doi)
            return edit

    def test_add_arxiv(self):
        # Dissemin has the first two authors in reversed order but Unpaywall still finds it
        edit = self.propose_change("""
{{Cite journal|last=Prpić|first=John|last2=Shukla|first2=Prashant P.|last3=Kietzmann|first3=Jan H.|last4=McCarthy|first4=Ian P.|date=2015-01-01|title=How to work a crowd: Developing crowd capital through
crowdsourcing|url=http://www.sciencedirect.com/science/article/pii/S0007681314001438|journal=Business Horizons|volume=58|issue=1|pages=77–85|doi=10.1016/j.bushor.2014.09.005}}
        """)
        self.assertEquals("arxiv=1702.04214", edit.proposed_change)

    # Test ability to find the PMC ID in case with multiple issues:
    # Dissemin returns 1 dead publisher URL, 3 PMC URLs and 1 PMID URL
    def test_add_pmc(self):
        edit = self.propose_change("""
{{Cite journal|doi=10.4103/0973-7847.112853|title=Phytochemistry and medicinal properties of Phaleria macrocarpa (Scheff.) Boerl. Extracts|journal=Pharmacognosy Reviews|volume=7|issue=13|pages=73–80|year=2013|last1=Altaf|first1=Rabia}}
        """)
        self.assertEquals("pmc=3731883", edit.proposed_change)

    # Test a title and DOI which is not OA and on Dissemin is
    # merged with many similar ones, related but not the same.
    def test_similartitle(self):
        edit = self.propose_change("""
{{cite journal  |vauthors=Marsh SG, Albert ED, Bodmer WF, etal | title = Nomenclature for factors of the HLA system, 2004 | journal = Tissue Antigens | volume = 65 | issue = 4 | pages = 301–69 | year = 2005 | pmid = 15787720 | doi = 10.1111/j.1399-0039.2005.00379.x }}
        """)
        self.assertEquals("", edit.proposed_change)

    # Test a dead URL
    def test_add_naldc(self):
        edit = self.propose_change("""
{{cite journal|doi=10.1016/j.chroma.2005.05.009|pmid=16007998|title=Determination of citrulline in watermelon rind|journal=Journal of Chromatography A|volume=1078|issue=1–2|pages=196–200|year=2005|last1=Rimando|first1=Agnes M.}}
        """)
        self.assertNotEquals("url=https://naldc.nal.usda.gov/naldc/download.xhtml?id=42375&content=PDF", edit.proposed_change)

    # Test add handle and hdl-access
    def test_add_hdl(self):
        edit = self.propose_change("""
{{cite journal|doi=10.1006/mcpr.2001.0377|pmid=11851384|title=C306A single nucleotide polymorphism in the human CEBPD gene that maps at 8p11.1–p11.2|journal=Molecular and Cellular Probes|volume=15|issue=6|pages=395–397|year=2002|last1=Angeloni|first1=Debora|last2=Lee|first2=Joshua D.}}
        """)
        self.assertEquals("hdl=11382/3170|hdl-access=free", edit.proposed_change)

    # Non-OA paper, expecting URL https://deepblue.lib.umich.edu/bitstream/2027.42/73088/1/j.1096-0031.1992.tb00073.x.pdf
    def test_existing_hdl(self):
        edit = self.propose_change("""
{{cite journal |author=Naylor, G.J.P. |title=The phylogenetic relationships among requiem and hammerhead sharks: inferring phylogeny when thousands of equally most parsimonious trees result |journal=Cladistics |volume=8 |date=1992 |pages=295&ndash;318 |doi=10.1111/j.1096-0031.1992.tb00073.x |issue=4|hdl=2027.42/73088 }}
        """)
        self.assertEquals("hdl-access=free", edit.proposed_change)

    # Do not add URL redundant with existing DOI even if doi-access missing
    def test_existing_oadoi(self):
        edit = self.propose_change("""
{{cite journal |last1=Blakeslee |first1=April M. H. |title=Assessing the Effects of Trematode Infection on Invasive Green Crabs in Eastern North America |journal=PLOS ONE |date=1 June 2015 |volume=10 |issue=6 |doi=10.1371/journal.pone.0128674 }}
        """, only_doi=True)
        self.assertEquals("doi-access=free", edit.proposed_change)

    def test_uppercase(self):
        edit = self.propose_change("""
{{Cite journal|last=Prpić|first=John|last2=Shukla|first2=Prashant P.|last3=Kietzmann|first3=Jan H.|last4=McCarthy|first4=Ian P.|date=2015-01-01|title=How to work a crowd: Developing crowd capital through
crowdsourcing|url=http://www.sciencedirect.com/science/article/pii/S0007681314001438|journal=Business Horizons|volume=58|issue=1|pages=77–85|doi=10.1016/j.bushor.2014.09.005|ARXIV=1702.04214}}
        """)
        self.assertEquals('', edit.proposed_change)

    # Test a book which is not open access but has a review which is
    def test_book(self):
        edit = self.propose_change("""
{{Citation |last=Kandel |first=Eric R. |year=2012 |title=The Age of Insight: The Quest to Understand the Unconscious in Art, Mind, and Brain, from Vienna 1900 to the Present |publisher=Random House|location=New York |isbn=978-1-4000-6871-5}}"
        """)
        self.assertEquals('', edit.proposed_change)


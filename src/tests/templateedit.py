# -*- encoding: utf-8 -*-


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
        # Paper also on Dissemin but without arxiv link as of 2020-05
        edit = self.propose_change("""
{{Cite journal|last=McLachlan|first=Robert I.|last2=Offen|first2=Christian|date=2019|title=Symplectic integration of boundary value problems|journal=Numerical Algorithms|language=en|volume=81|issue=4|pages=1219–1233|doi=10.1007/s11075-018-0599-7}}
        """)
        self.assertEqual("arxiv=1804.09042", edit.proposed_change)

    # Test ability to find the PMC ID in case with multiple issues:
    # Dissemin returns 1 dead publisher URL, 3 PMC URLs and 1 PMID URL
    def test_add_pmc(self):
        edit = self.propose_change("""
{{Cite journal|doi=10.4103/0973-7847.112853|title=Phytochemistry and medicinal properties of Phaleria macrocarpa (Scheff.) Boerl. Extracts|journal=Pharmacognosy Reviews|volume=7|issue=13|pages=73–80|year=2013|last1=Altaf|first1=Rabia}}
        """)
        self.assertEqual("pmc=3731883", edit.proposed_change)

    # Test a title and DOI which is not OA and on Dissemin is
    # merged with many similar ones, related but not the same.
    def test_similartitle(self):
        edit = self.propose_change("""
{{cite journal  |vauthors=Marsh SG, Albert ED, Bodmer WF, etal | title = Nomenclature for factors of the HLA system, 2004 | journal = Tissue Antigens | volume = 65 | issue = 4 | pages = 301–69 | year = 2005 | pmid = 15787720 | doi = 10.1111/j.1399-0039.2005.00379.x }}
        """)
        self.assertEqual("", edit.proposed_change)

    # Test a dead URL
    def test_add_naldc(self):
        edit = self.propose_change("""
{{cite journal|doi=10.1016/j.chroma.2005.05.009|pmid=16007998|title=Determination of citrulline in watermelon rind|journal=Journal of Chromatography A|volume=1078|issue=1–2|pages=196–200|year=2005|last1=Rimando|first1=Agnes M.}}
        """)
        self.assertNotEqual("url=https://naldc.nal.usda.gov/naldc/download.xhtml?id=42375&content=PDF", edit.proposed_change)

    # Test add handle and hdl-access
    def test_add_hdl(self):
        edit = self.propose_change("""
{{cite journal|last1=Fraass|first1=Benedick A.|title=The development of conformal radiation therapy|journal=Medical Physics|date=1995|volume=22|issue=11|pages=1911–1921|doi=10.1118/1.597446|pmid=8587545}}
        """)
        self.assertEqual("hdl=2027.42/134769|hdl-access=free", edit.proposed_change)

    # Non-OA paper, expecting URL https://deepblue.lib.umich.edu/bitstream/2027.42/73088/1/j.1096-0031.1992.tb00073.x.pdf
    def test_existing_hdl(self):
        edit = self.propose_change("""
{{cite journal |author=Naylor, G.J.P. |title=The phylogenetic relationships among requiem and hammerhead sharks: inferring phylogeny when thousands of equally most parsimonious trees result |journal=Cladistics |volume=8 |date=1992 |pages=295&ndash;318 |doi=10.1111/j.1096-0031.1992.tb00073.x |issue=4|hdl=2027.42/73088 }}
        """)
        self.assertEqual("hdl-access=free", edit.proposed_change)

    # Do not add URL redundant with existing DOI even if doi-access missing
    def test_existing_oadoi(self):
        edit = self.propose_change("""
{{cite journal |last1=Blakeslee |first1=April M. H. |title=Assessing the Effects of Trematode Infection on Invasive Green Crabs in Eastern North America |journal=PLOS ONE |date=1 June 2015 |volume=10 |issue=6 |doi=10.1371/journal.pone.0128674 }}
        """, only_doi=True)
        self.assertEqual("doi-access=free", edit.proposed_change)

    def test_uppercase_arxiv(self):
        edit = self.propose_change("""
{{Cite journal|last=Prpić|first=John|last2=Shukla|first2=Prashant P.|last3=Kietzmann|first3=Jan H.|last4=McCarthy|first4=Ian P.|date=2015-01-01|title=How to work a crowd: Developing crowd capital through
crowdsourcing|url=http://www.sciencedirect.com/science/article/pii/S0007681314001438|journal=Business Horizons|volume=58|issue=1|pages=77–85|doi=10.1016/j.bushor.2014.09.005|ARXIV=1702.04214}}
        """)
        self.assertEqual('', edit.proposed_change)

    # Test a book which is not open access but has a review which is
    def test_book(self):
        edit = self.propose_change("""
{{Citation |last=Kandel |first=Eric R. |year=2012 |title=The Age of Insight: The Quest to Understand the Unconscious in Art, Mind, and Brain, from Vienna 1900 to the Present |publisher=Random House|location=New York |isbn=978-1-4000-6871-5}}"
        """)
        self.assertEqual('', edit.proposed_change)

    def test_closed_url_access(self):
        edit = self.propose_change("""
{{cite journal |last1=de Janvry |first1=Alain |last2=Sadoulet |first2=Elisabeth |title=Income Strategies Among Rural Households in Mexico: The Role of Off-farm Activities |journal=World Development |date=1 March 2001 |volume=29 |issue=3 |pages=467–480 |doi=10.1016/S0305-750X(00)00113-3 |url=https://www.sciencedirect.com/science/article/abs/pii/S0305750X00001133 |language=en |issn=0305-750X}}"
        """)
        self.assertEqual('url-access=subscription|', edit.proposed_change)

    # Don't add an url-access parameter if there is one already.
    def test_existing_url_access(self):
        edit = self.propose_change("""
{{Citation  | last = Peggy  | first = Klaus  | title = The Hard Truth About Soft Skills: Workplace Lessons Smart People Wish They'd Learned Sooner  | publisher = HarperCollins  | year = 2008  | isbn = 978-0-061-28414-4  | url-access = registration  | url = https://archive.org/details/hardtruthaboutso00klau  }}"
        """)
        self.assertEqual('', edit.proposed_change)

    # Don't make changes for a seemingly closed DOI with a functioning PDF link.
    def test_existing_url_closed_access(self):
        edit = self.propose_change("""
{{cite journal |last1=Shepard |first1=William |last2=Marquardt |first2=H. Michael |title=Lyman E. Johnson: Forgotten Apostle |journal=[[Journal of Mormon History]] |date=Winter 2010 |volume=36 |issue=1 |page=93 |doi=10.2307/23291073 |jstor=23291073 |url=https://digitalcommons.usu.edu/cgi/viewcontent.cgi?referer=&httpsredir=1&article=1052&context=mormonhistory |access-date=6 May 2021 }}
        """)
        self.assertEqual('', edit.proposed_change)

    # Add a PMC identifier even if the DOI is gold OA.
    def test_add_pmc_gold_oa(self):
        edit = self.propose_change("""
{{cite journal | last1=Lit | first1=Lisa | title=Differences in Behavior and Activity Associated with a Poly(A) Expansion in the Dopamine Transporter in Belgian Malinois | journal=PLOS ONE | publisher=Public Library of Science (PLoS) | volume=8 | issue=12 | date=23 Dec 2013 | issn=1932-6203 | doi=10.1371/journal.pone.0082948 | page=e82948 | doi-access=free | pmid=24376613 }}
        """)
        self.assertEqual('pmc=3871558', edit.proposed_change)

    # T354471: Ignore arxiv URL from CiteSeerX
    def test_add_no_arxiv_from_citeseerx(self):
        edit = self.propose_change("""
{{Cite journal |last=S. |first=D. |date=1966 |title=Review of Mathematical Methods in Physics |journal=Mathematics of Computation |volume=20 |issue=93 |pages=188–189 |doi=10.2307/2004316 |jstor=2004316 |issn=0025-5718 }}
        """)
        self.assertNotEqual('arxiv=hep-th/0502233', edit.proposed_change)

    def test_add_arxiv_from_citeseerx(self):
        edit = self.propose_change("""
{{cite journal|first1=Aris|last1=Anagnostopoulos|first2=Ioannis|last2=Kontoyiannis|first3=Eli|last3=Upfal|title=Steady state analysis of balanced‐allocation routing|journal=Random Structures & Algorithms|date=2005-07|pages=446–467|volume=26|issue=4|doi=10.1002/rsa.20071}}
        """)
        self.assertEqual('arxiv=0209357', edit.proposed_change)

    def test_add_pmc_dupe_title(self):
        edit = self.propose_change("""
{{cite journal|title=New properties of all real functions|first=Henry|last=Blumberg|journal=Proceedings of the National Academy of Sciences|volume=8|issue=1|year=1922|pages=283–288 |doi=10.1073/pnas.8.10.283 |pmid=16586898 |doi-access=free }}
        """)
        self.assertEqual('pmc=1085149', edit.proposed_change)

    def test_add_no_pmc_dupe_title(self):
        edit = self.propose_change("""
{{cite journal|title=New properties of all real functions|first=Henry|last=Blumberg|journal=Transactions of the American Mathematical Society|volume=24|date=September 1922|issue=2|page=113-128|doi=10.1090/S0002-9947-1922-1501216-9|doi-access=free|jstor=1989037|jstor-access=free}}
        """)
        self.assertNotEqual('pmc=1085149', edit.proposed_change)

# -*- encoding: utf-8 -*-


import unittest

from oabot.arguments import *

class ArgumentTests(unittest.TestCase):
    def test_doi(self):
        self.assertEqual('10.4230/LIPIcs.FSCD.2018.23', doi_argument.extract('https://dx.doi.org/10.4230/LIPIcs.FSCD.2018.23'))
        self.assertEqual('10.4230/LIPIcs.FSCD.2018.23', doi_argument.extract('http://doi.org/10.4230/LIPIcs.FSCD.2018.23'))

    def test_hdl(self):
        self.assertEqual('1854/LU-4110028', hdl_argument.extract('https://hdl.handle.net/1854/LU-4110028'))

    def test_arxiv(self):
        self.assertEqual('alg-geom/9702012', arxiv_argument.extract('http://arxiv.org/abs/alg-geom/9702012'))
        self.assertEqual('alg-geom/9702012', arxiv_argument.extract('http://arxiv.org/pdf/alg-geom/9702012'))
        self.assertEqual('alg-geom/9702012', arxiv_argument.extract('http://arxiv.org/pdf/alg-geom/9702012.pdf'))

    def test_pmc(self):
        self.assertEqual('5739466', pmc_argument.extract('https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5739466/'))

    def test_eupmc(self):
        self.assertEqual('5739466', eupmc_argument.extract('https://europepmc.org/articles/pmc5739466'))

    def test_citeseerx(self):
        self.assertEqual('10.1.1.492.3416', citeseerx_argument.extract('http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.492.3416'))
        self.assertEqual('10.1.1.492.3416', citeseerx_argument.extract('http://citeseerx.ist.psu.edu/viewdoc/download?doi=10.1.1.492.3416&rep=rep1&type=pdf'))

    def test_url(self):
        self.assertEqual('http://eprints.keele.ac.uk/788/', url_argument.extract('http://eprints.keele.ac.uk/788/'))

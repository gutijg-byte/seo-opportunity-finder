import tempfile
import unittest
from pathlib import Path

from seo_opportunities import Query, load_queries, main, rank_queries, spreadsheet_safe


class OpportunityTests(unittest.TestCase):
    def load(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'queries.csv'
            path.write_text(content, encoding='utf-8-sig')
            return load_queries(path)

    def test_spanish_decimal_comma(self):
        rows = self.load('Consultas principales;Clics;Impresiones;Posición\nseo;20;1000;8,5\n')
        self.assertEqual(rows[0].position, 8.5)
        self.assertEqual(rows[0].ctr, 0.02)

    def test_english_and_ignored_rounded_ctr(self):
        rows = self.load('Top queries,Clicks,Impressions,CTR,Position\nseo,20,1000,1%,8\n')
        self.assertEqual(rows[0].ctr, 0.02)

    def test_gaps_filters_order_and_brand_exclusion(self):
        data = [Query('seo', 20, 1000, 8), Query('python', 10, 2000, 10),
                Query('marca seo', 0, 9000, 5), Query('low', 0, 10, 4),
                Query('high ctr', 100, 1000, 7), Query('far', 0, 5000, 30)]
        rows = rank_queries(data, exclude=['MARCA'])
        self.assertEqual([row['query'] for row in rows], ['python', 'seo'])
        self.assertEqual([row['scenario_click_gap'] for row in rows], [90, 30])

    def test_bad_values(self):
        for row in ['seo,-1,100,8', 'seo,101,100,8', 'seo,1,100,nan',
                    'seo,1,100,inf', 'seo,1,100,0', ',1,100,8']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                self.load('query,clicks,impressions,position\n' + row + '\n')

    def test_duplicate_queries(self):
        with self.assertRaises(ValueError):
            self.load('query,clicks,impressions,position\nseo,1,100,8\nseo,2,200,9\n')

    def test_wrong_dimension(self):
        with self.assertRaises(ValueError):
            self.load('page,clicks,impressions,position\nhttps://example.com,1,100,8\n')

    def test_zero_impressions(self):
        self.assertEqual(rank_queries([Query('seo', 0, 0, 1)]), [])

    def test_invalid_parameters(self):
        for kwargs in [{'target_ctr': float('nan')}, {'target_ctr': 2},
                       {'min_position': 20, 'max_position': 4}, {'min_impressions': 0}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                rank_queries([], **kwargs)

    def test_formula_protection(self):
        self.assertEqual(spreadsheet_safe(' =1+1'), "' =1+1")
        self.assertEqual(spreadsheet_safe('seo'), 'seo')

    def test_cli_and_overwrite_protection(self):
        with tempfile.TemporaryDirectory() as directory:
            source, output = Path(directory) / 'in.csv', Path(directory) / 'out.csv'
            source.write_text('query,clicks,impressions,position\nseo,20,1000,8\n')
            args = [str(source), '--output', str(output)]
            self.assertEqual(main(args), 0)
            before = output.read_bytes()
            self.assertEqual(main(args), 2)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(main([str(source), '--output', str(source)]), 2)


if __name__ == '__main__':
    unittest.main()

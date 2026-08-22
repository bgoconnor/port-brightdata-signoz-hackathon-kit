import os
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from .models import Paper, ScrapeRun
from .services import refresh_scrape, start_scrape


BRIGHT_ENV = {
    'BRIGHTDATA_API_KEY': 'test-key',
    'BRIGHTDATA_COLLECTOR_ID': 'c_test',
}


class ScrapeLifecycleTests(TestCase):
    @patch.dict(os.environ, BRIGHT_ENV)
    @patch('scraper.services._request_json')
    def test_completed_run_ingests_papers(self, request_json):
        request_json.side_effect = [
            {'collection_id': 'j_test'},
            {
                'status': 'done',
                'lines': 1,
                'fails': 0,
                'started': '2026-08-22T21:00:00Z',
                'finished': '2026-08-22T21:01:00Z',
            },
            [{
                'arxiv_id': '2608.00001',
                'title': 'We propose a toy algorithm',
                'authors': ['Ada Lovelace'],
                'abstract': 'A synthetic experiment with a complexity result.',
                'subjects': ['cs.AI'],
            }],
        ]

        run = refresh_scrape(start_scrape())

        self.assertEqual(run.status, ScrapeRun.Status.COMPLETED)
        self.assertEqual(run.records_written, 1)
        paper = Paper.objects.get(arxiv_id='2608.00001')
        self.assertTrue(paper.reproducible)
        self.assertEqual(paper.authors, ['Ada Lovelace'])

    @patch.dict(os.environ, BRIGHT_ENV)
    @patch('scraper.services._request_json')
    def test_invalid_result_fails_without_partial_write(self, request_json):
        request_json.side_effect = [
            {'collection_id': 'j_invalid'},
            {'status': 'done', 'lines': 1, 'fails': 0},
            [{'arxiv_id': '2608.00002'}],
        ]

        run = refresh_scrape(start_scrape())

        self.assertEqual(run.status, ScrapeRun.Status.FAILED)
        self.assertIn('missing required fields', run.error)
        self.assertEqual(Paper.objects.count(), 0)


class PaperApiTests(TestCase):
    def test_paper_list_returns_article_contract(self):
        Paper.objects.create(
            arxiv_id='2608.00003',
            title='A paper',
            authors=['Grace Hopper'],
            abstract='An abstract',
            subjects=['cs.AI'],
            score=0.72,
            reproducible=True,
            scraped_at=timezone.now(),
        )

        response = self.client.get('/api/papers/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['count'], 1)
        self.assertEqual(response.json()['papers'][0]['arxiv_id'], '2608.00003')

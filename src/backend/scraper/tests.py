import os
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from .models import Paper, ScrapeRun
from .services import refresh_scrape, start_enrichment, start_scrape


BRIGHT_ENV = {
    'BRIGHTDATA_API_KEY': 'test-key',
    'BRIGHTDATA_COLLECTOR_ID': 'c_test',
}

FULLTEXT_ENV = {
    **BRIGHT_ENV,
    'BRIGHTDATA_FULLTEXT_COLLECTOR_ID': 'c_fulltext',
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


class EnrichmentLifecycleTests(TestCase):
    def setUp(self):
        self.paper = Paper.objects.create(
            arxiv_id='2608.00004',
            title='A paper requiring its methods section',
            authors=['Katherine Johnson'],
            abstract='An abstract is not enough.',
            subjects=['cs.AI'],
            score=0.7,
            reproducible=True,
            scraped_at=timezone.now(),
        )

    @patch.dict(os.environ, FULLTEXT_ENV)
    @patch('scraper.services._request_json')
    def test_hosted_collector_result_is_persisted_on_paper(self, request_json):
        full_text = ('# Paper\n\n' + ('Methods and evidence. ' * 80)).strip()
        request_json.side_effect = [
            {'collection_id': 'j_fulltext'},
            {'status': 'done', 'lines': 1, 'fails': 0},
            [{'markdown': full_text}],
        ]

        run = refresh_scrape(start_enrichment(self.paper))

        self.assertEqual(run.kind, ScrapeRun.Kind.ENRICHMENT)
        self.assertEqual(run.status, ScrapeRun.Status.COMPLETED)
        self.paper.refresh_from_db()
        self.assertEqual(self.paper.full_text, full_text)
        self.assertEqual(self.paper.full_text_collection_id, 'j_fulltext')
        self.assertEqual(len(self.paper.full_text_sha256), 64)
        request_json.assert_any_call(
            'POST',
            '/dca/trigger?collector=c_fulltext&queue_next=1',
            [{'url': 'https://arxiv.org/html/2608.00004'}],
        )

    @patch.dict(os.environ, FULLTEXT_ENV)
    @patch('scraper.services._request_json')
    def test_invalid_fulltext_does_not_replace_existing_content(self, request_json):
        self.paper.full_text = 'existing canonical content'
        self.paper.save(update_fields=('full_text',))
        request_json.side_effect = [
            {'collection_id': 'j_short'},
            {'status': 'done', 'lines': 1, 'fails': 0},
            [{'markdown': 'too short'}],
        ]

        run = refresh_scrape(start_enrichment(self.paper))

        self.assertEqual(run.status, ScrapeRun.Status.FAILED)
        self.paper.refresh_from_db()
        self.assertEqual(self.paper.full_text, 'existing canonical content')

    @patch.dict(os.environ, FULLTEXT_ENV)
    @patch('scraper.services._request_json')
    def test_enrichment_endpoint_starts_hosted_job(self, request_json):
        request_json.return_value = {'collection_id': 'j_api'}

        response = self.client.post('/api/papers/2608.00004/enrich/')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()['run']['kind'], 'enrichment')
        self.assertEqual(response.json()['run']['paper'], '2608.00004')

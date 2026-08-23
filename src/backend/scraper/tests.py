import json
import os
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from .models import DemoSite, Paper, ScrapeRun
from .management.commands.build_demo_site import _validate_html
from .services import _normalize_record, refresh_scrape, start_scrape


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
                'source_url': 'https://arxiv.org/abs/2608.00001',
                'full_text': '# Paper\n' + ('Methods and results. ' * 80),
            }],
        ]

        run = refresh_scrape(start_scrape())

        self.assertEqual(run.status, ScrapeRun.Status.COMPLETED)
        self.assertEqual(run.records_written, 1)
        paper = Paper.objects.get(arxiv_id='2608.00001')
        self.assertEqual(paper.paper_id, 'arxiv:2608.00001')
        self.assertEqual(paper.source, 'arxiv')
        self.assertTrue(paper.reproducible)
        self.assertEqual(paper.authors, ['Ada Lovelace'])
        self.assertGreater(len(paper.full_text), 1000)
        self.assertEqual(paper.full_text_collection_id, 'j_test')
        self.assertEqual(len(paper.full_text_sha256), 64)

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
            paper_id='arxiv:2608.00003',
            source='arxiv',
            source_id='2608.00003',
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


class MultiSourceTests(TestCase):
    def test_company_publication_gets_source_qualified_identity(self):
        record = _normalize_record({
            'source_id': 'teaching-claude-why',
            'title': 'Teaching Claude why',
            'authors': [],
            'abstract': 'An explicit research summary.',
            'subjects': ['Alignment'],
            'published_at': '2026-05-08T00:00:00Z',
            'source_url': 'https://www.anthropic.com/research/teaching-claude-why',
            'full_text': 'Methods and evidence. ' * 80,
        }, timezone.now(), 'anthropic')

        self.assertEqual(record['paper_id'], 'anthropic:teaching-claude-why')
        self.assertIsNone(record['arxiv_id'])
        self.assertEqual(record['authors'], ['Anthropic'])
        self.assertIsNotNone(record['published_at'])

    @patch.dict(os.environ, {
        'BRIGHTDATA_API_KEY': 'test-key',
        'BRIGHTDATA_ANTHROPIC_COLLECTOR_ID': 'c_anthropic',
    })
    @patch('scraper.services._request_json')
    def test_anthropic_run_uses_its_hosted_collector(self, request_json):
        request_json.return_value = {'collection_id': 'j_anthropic'}

        run = start_scrape('anthropic')

        self.assertEqual(run.source, 'anthropic')
        self.assertEqual(run.collector_id, 'c_anthropic')
        self.assertEqual(run.target_url, 'https://www.anthropic.com/research')
        request_json.assert_called_once()


class DemoSiteApiTests(TestCase):
    def setUp(self):
        self.paper = Paper.objects.create(
            paper_id='arxiv:2608.00004',
            source='arxiv',
            source_id='2608.00004',
            arxiv_id='2608.00004',
            title='A Port hello paper',
            authors=['Test Author'],
            abstract='An abstract',
            full_text='Full methods and evidence. ' * 80,
            subjects=['cs.AI'],
            score=0.5,
            reproducible=True,
            scraped_at=timezone.now(),
        )

    @patch('scraper.views.create_demo_site_job', return_value='demo-site-123456789abc')
    def test_post_creates_kubernetes_job(self, create_job):
        response = self.client.post(
            '/api/demo-sites/build/',
            data=json.dumps({'paper_id': self.paper.paper_id}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.json()['job_name'], 'demo-site-123456789abc')
        create_job.assert_called_once_with(self.paper.paper_id)
        self.assertEqual(self.paper.demo_site.status, DemoSite.Status.QUEUED)

    def test_unknown_paper_returns_not_found(self):
        response = self.client.post(
            '/api/demo-sites/build/',
            data=json.dumps({'paper_id': 'arxiv:missing'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 404)

    def test_abstract_only_paper_is_rejected(self):
        self.paper.full_text = ''
        self.paper.save(update_fields=['full_text'])

        response = self.client.post(
            '/api/demo-sites/build/',
            data=json.dumps({'paper_id': self.paper.paper_id}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn('no full text', response.json()['error'])

    def test_ready_site_is_served_with_restrictive_csp(self):
        DemoSite.objects.create(
            paper=self.paper,
            status=DemoSite.Status.READY,
            html='<!doctype html><html><body><button>Demo</button></body></html>',
        )

        response = self.client.get(f'/api/demo-sites/{self.paper.paper_id}/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/html; charset=utf-8')
        self.assertIn("default-src 'none'", response['Content-Security-Policy'])
        self.assertEqual(response['X-Frame-Options'], 'SAMEORIGIN')

        detail = self.client.get(f'/api/papers/{self.paper.paper_id}/').json()
        self.assertEqual(detail['demo_site']['status'], DemoSite.Status.READY)
        self.assertEqual(
            detail['demo_site']['site_url'],
            f'/api/demo-sites/{self.paper.paper_id}/',
        )

    def test_validator_rejects_external_assets(self):
        html = (
            '<!doctype html><html><body>'
            '<script src="https://example.com/app.js"></script>'
            + ('interactive explanation ' * 50)
            + '</body></html>'
        )

        self.assertIn(
            'External network asset detected; all assets must be inline.',
            _validate_html(html),
        )

    def test_validator_allows_external_citation_links(self):
        html = (
            '<!doctype html><html><body>'
            '<a href="https://arxiv.org/abs/2608.19202">paper</a><script>document.body.dataset.ready="1"</script>'
            + ('interactive explanation ' * 50)
            + '</body></html>'
        )

        self.assertEqual(_validate_html(html), [])

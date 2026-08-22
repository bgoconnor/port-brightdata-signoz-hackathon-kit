import time

from django.core.management.base import BaseCommand, CommandError

from scraper.models import Paper, ScrapeRun
from scraper.services import refresh_scrape, start_enrichment


class Command(BaseCommand):
    help = 'Run the hosted Bright Data full-text collector and persist its result.'

    def add_arguments(self, parser):
        parser.add_argument('arxiv_id')
        parser.add_argument('--poll-interval', type=float, default=5)
        parser.add_argument('--timeout', type=int, default=600)

    def handle(self, *args, **options):
        try:
            paper = Paper.objects.get(pk=options['arxiv_id'])
        except Paper.DoesNotExist as error:
            raise CommandError('Paper must be discovered before it can be enriched') from error

        run = start_enrichment(paper)
        if run.status == ScrapeRun.Status.FAILED:
            raise CommandError(run.error)
        self.stdout.write(f'Triggered Bright Data full-text job {run.bright_job_id}')

        deadline = time.monotonic() + options['timeout']
        while time.monotonic() < deadline:
            run = refresh_scrape(run)
            if run.status == ScrapeRun.Status.COMPLETED:
                self.stdout.write(self.style.SUCCESS(
                    f'Persisted full text for {paper.arxiv_id} from {run.bright_job_id}'
                ))
                return
            if run.status in {ScrapeRun.Status.FAILED, ScrapeRun.Status.CANCELED}:
                raise CommandError(run.error or f'Enrichment ended with status {run.status}')
            time.sleep(options['poll_interval'])
        raise CommandError(f'Timed out waiting for {run.bright_job_id}')

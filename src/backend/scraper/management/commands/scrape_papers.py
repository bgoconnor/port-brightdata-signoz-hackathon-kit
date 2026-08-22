import time

from django.core.management.base import BaseCommand, CommandError

from scraper.models import ScrapeRun
from scraper.services import refresh_scrape, start_scrape


class Command(BaseCommand):
    help = 'Run the configured Bright Data collector and ingest its papers.'

    def add_arguments(self, parser):
        parser.add_argument('--poll-interval', type=float, default=5)
        parser.add_argument('--timeout', type=int, default=600)

    def handle(self, *args, **options):
        run = start_scrape()
        if run.status == ScrapeRun.Status.FAILED:
            raise CommandError(run.error)
        self.stdout.write(f'Triggered Bright Data job {run.bright_job_id}')

        deadline = time.monotonic() + options['timeout']
        while time.monotonic() < deadline:
            run = refresh_scrape(run)
            if run.status == ScrapeRun.Status.COMPLETED:
                self.stdout.write(self.style.SUCCESS(
                    f'Ingested {run.records_written} papers from {run.bright_job_id}'
                ))
                return
            if run.status in {ScrapeRun.Status.FAILED, ScrapeRun.Status.CANCELED}:
                raise CommandError(run.error or f'Scrape ended with status {run.status}')
            time.sleep(options['poll_interval'])

        raise CommandError(f'Timed out waiting for {run.bright_job_id}')

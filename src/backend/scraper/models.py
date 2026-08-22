from django.db import models

# TODO: Create a document model based off of the bright data repo article outputs.


class Paper(models.Model):
    arxiv_id = models.CharField(max_length=32, primary_key=True)
    title = models.TextField()
    authors = models.JSONField()
    abstract = models.TextField()
    subjects = models.JSONField()
    score = models.FloatField()
    reproducible = models.BooleanField()
    scraped_at = models.DateTimeField()
    full_text = models.TextField(blank=True)
    full_text_source_url = models.URLField(max_length=500, blank=True)
    full_text_sha256 = models.CharField(max_length=64, blank=True)
    full_text_acquired_at = models.DateTimeField(null=True, blank=True)
    full_text_collection_id = models.CharField(max_length=64, blank=True)


class ScrapeRun(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        COLLECTING = 'collecting', 'Collecting'
        PAUSED = 'paused', 'Paused'
        INGESTING = 'ingesting', 'Ingesting'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELED = 'canceled', 'Canceled'

    collector_id = models.CharField(max_length=64)
    target_url = models.URLField(max_length=500)
    bright_job_id = models.CharField(max_length=64, unique=True, null=True, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.SUBMITTED)
    bright_status = models.CharField(max_length=32, blank=True)
    records_received = models.PositiveIntegerField(default=0)
    records_written = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    bright_started_at = models.DateTimeField(null=True, blank=True)
    bright_finished_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.bright_job_id or f'Scrape run {self.pk}'

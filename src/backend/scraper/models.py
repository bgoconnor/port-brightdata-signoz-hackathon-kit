from django.db import models

# TODO: Create a document model based off of the bright data repo article outputs.


class Paper(models.Model):
    """A scraped research paper.

    `status` mirrors the Port `paper` blueprint enum; Port remains the system of
    record and this column is a read-through cache for the 4s frontend poll.
    """

    class Status(models.TextChoices):
        INGESTED = 'ingested', 'Ingested'
        QUEUED = 'queued', 'Queued'
        GENERATING = 'generating', 'Generating'
        AWAITING_REVIEW = 'awaiting_review', 'Awaiting review'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    paper_id = models.CharField(max_length=300, primary_key=True)
    source = models.CharField(max_length=32, default='arxiv')
    source_id = models.CharField(max_length=255)
    arxiv_id = models.CharField(max_length=32, null=True, blank=True, unique=True)
    title = models.TextField()
    authors = models.JSONField()
    abstract = models.TextField()
    subjects = models.JSONField()
    published_at = models.DateTimeField(null=True, blank=True)
    pdf_url = models.URLField(max_length=500, blank=True)
    score = models.FloatField()
    reproducible = models.BooleanField()
    scraped_at = models.DateTimeField()
    full_text = models.TextField(blank=True)
    full_text_source_url = models.URLField(max_length=500, blank=True)
    full_text_sha256 = models.CharField(max_length=64, blank=True)
    full_text_acquired_at = models.DateTimeField(null=True, blank=True)
    full_text_collection_id = models.CharField(max_length=64, blank=True)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.INGESTED
    )
    retry_count = models.PositiveIntegerField(default=0)
    source_url = models.URLField(max_length=500, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=('source', 'source_id'), name='unique_paper_source_id'),
        ]


class ScrapeRun(models.Model):
    class Status(models.TextChoices):
        SUBMITTED = 'submitted', 'Submitted'
        COLLECTING = 'collecting', 'Collecting'
        PAUSED = 'paused', 'Paused'
        INGESTING = 'ingesting', 'Ingesting'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        CANCELED = 'canceled', 'Canceled'

    source = models.CharField(max_length=32, default='arxiv')
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


class Reproduction(models.Model):
    """Mirror of the Port `reproduction` blueprint for one paper.

    Port owns the lifecycle; this is written by the sync layer so the detail
    endpoint can serve the whole payload in one query.
    """

    class RunStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PASSED = 'passed', 'Passed'
        FAILED = 'failed', 'Failed'

    paper = models.OneToOneField(
        Paper, on_delete=models.CASCADE, related_name='reproduction'
    )
    port_entity_id = models.CharField(max_length=128, blank=True)
    generated_code = models.TextField(blank=True)
    run_output = models.TextField(blank=True)
    run_status = models.CharField(
        max_length=16, choices=RunStatus.choices, default=RunStatus.PENDING
    )
    retry_count = models.PositiveIntegerField(default=0)
    repro_summary = models.TextField(blank=True)
    evidence_url = models.URLField(max_length=500, blank=True)
    # repro_result -> {"claimed": str, "measured": str, "reproduced": bool}
    repro_result = models.JSONField(null=True, blank=True)
    review_note = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Reproduction for {self.paper_id}'


class Attempt(models.Model):
    """One execution of a generated candidate.

    Every attempt is retained, including failures with their traceback. The
    attempt-history UI renders failed attempts expanded, so they must survive.
    """

    class Status(models.TextChoices):
        PASSED = 'passed', 'Passed'
        FAILED = 'failed', 'Failed'

    reproduction = models.ForeignKey(
        Reproduction, on_delete=models.CASCADE, related_name='attempts'
    )
    index = models.PositiveIntegerField()
    status = models.CharField(max_length=16, choices=Status.choices)
    code = models.TextField(blank=True)
    output = models.TextField(blank=True)
    duration_s = models.FloatField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['index']
        unique_together = [('reproduction', 'index')]

    def __str__(self):
        return f'{self.reproduction.paper_id} attempt {self.index} ({self.status})'


class DemoSite(models.Model):
    """Latest website generated by Port for a paper and served by Django."""

    class Status(models.TextChoices):
        QUEUED = 'queued', 'Queued'
        GENERATING = 'generating', 'Generating'
        READY = 'ready', 'Ready'
        FAILED = 'failed', 'Failed'

    paper = models.OneToOneField(
        Paper, on_delete=models.CASCADE, related_name='demo_site'
    )
    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.QUEUED
    )
    html = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    iteration = models.PositiveIntegerField(default=0)
    port_workflow_run_id = models.CharField(max_length=64, blank=True)
    job_name = models.CharField(max_length=64, blank=True)
    error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class DemoSiteAttempt(models.Model):
    """Retained Port output and runtime observations for one generation attempt."""

    demo_site = models.ForeignKey(
        DemoSite, on_delete=models.CASCADE, related_name='attempts'
    )
    iteration = models.PositiveIntegerField()
    port_workflow_run_id = models.CharField(max_length=64)
    status = models.CharField(max_length=16)
    observations = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['iteration']
        unique_together = [('demo_site', 'iteration')]

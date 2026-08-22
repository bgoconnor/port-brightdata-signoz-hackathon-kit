from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScrapeRun',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('collector_id', models.CharField(max_length=64)),
                ('target_url', models.URLField(max_length=500)),
                ('bright_job_id', models.CharField(blank=True, max_length=64, null=True, unique=True)),
                ('status', models.CharField(choices=[('submitted', 'Submitted'), ('collecting', 'Collecting'), ('paused', 'Paused'), ('ingesting', 'Ingesting'), ('completed', 'Completed'), ('failed', 'Failed'), ('canceled', 'Canceled')], default='submitted', max_length=16)),
                ('bright_status', models.CharField(blank=True, max_length=32)),
                ('records_received', models.PositiveIntegerField(default=0)),
                ('records_written', models.PositiveIntegerField(default=0)),
                ('failure_count', models.PositiveIntegerField(default=0)),
                ('error', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bright_started_at', models.DateTimeField(blank=True, null=True)),
                ('bright_finished_at', models.DateTimeField(blank=True, null=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
    ]

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('scraper', '0006_paper_status_reproduction_attempt')]

    operations = [
        migrations.CreateModel(
            name='DemoSite',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('queued', 'Queued'), ('generating', 'Generating'), ('ready', 'Ready'), ('failed', 'Failed')], default='queued', max_length=16)),
                ('html', models.TextField(blank=True)),
                ('summary', models.TextField(blank=True)),
                ('iteration', models.PositiveIntegerField(default=0)),
                ('port_workflow_run_id', models.CharField(blank=True, max_length=64)),
                ('job_name', models.CharField(blank=True, max_length=64)),
                ('error', models.TextField(blank=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('paper', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='demo_site', to='scraper.paper')),
            ],
        ),
        migrations.CreateModel(
            name='DemoSiteAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('iteration', models.PositiveIntegerField()),
                ('port_workflow_run_id', models.CharField(max_length=64)),
                ('status', models.CharField(max_length=16)),
                ('observations', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('demo_site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attempts', to='scraper.demosite')),
            ],
            options={
                'ordering': ['iteration'],
                'unique_together': {('demo_site', 'iteration')},
            },
        ),
    ]

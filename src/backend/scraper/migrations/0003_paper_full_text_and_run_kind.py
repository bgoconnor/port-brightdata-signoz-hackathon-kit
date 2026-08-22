from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [('scraper', '0002_scraperun')]

    operations = [
        migrations.AddField(
            model_name='paper', name='full_text', field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='paper', name='full_text_source_url',
            field=models.URLField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='paper', name='full_text_sha256',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='paper', name='full_text_acquired_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='paper', name='full_text_collection_id',
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name='scraperun', name='kind',
            field=models.CharField(
                choices=[('discovery', 'Discovery'), ('enrichment', 'Enrichment')],
                default='discovery', max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='scraperun', name='paper',
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                related_name='scrape_runs', to='scraper.paper',
            ),
        ),
    ]

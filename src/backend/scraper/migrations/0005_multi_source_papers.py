from django.db import migrations, models


def namespace_existing_arxiv_papers(apps, schema_editor):
    Paper = apps.get_model('scraper', 'Paper')
    for paper in Paper.objects.all().iterator():
        old_id = paper.paper_id
        Paper.objects.filter(paper_id=old_id).update(
            paper_id=f'arxiv:{old_id}',
            source='arxiv',
            source_id=old_id,
            arxiv_id=old_id,
        )


class Migration(migrations.Migration):
    dependencies = [('scraper', '0004_single_collector_contract')]

    operations = [
        migrations.RenameField(model_name='paper', old_name='arxiv_id', new_name='paper_id'),
        migrations.AlterField(
            model_name='paper', name='paper_id',
            field=models.CharField(max_length=300, primary_key=True, serialize=False),
        ),
        migrations.AddField(model_name='paper', name='source', field=models.CharField(default='arxiv', max_length=32)),
        migrations.AddField(
            model_name='paper', name='source_id',
            field=models.CharField(default='', max_length=255), preserve_default=False,
        ),
        migrations.AddField(model_name='paper', name='arxiv_id', field=models.CharField(blank=True, max_length=32, null=True, unique=True)),
        migrations.AddField(model_name='paper', name='published_at', field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name='paper', name='pdf_url', field=models.URLField(blank=True, max_length=500)),
        migrations.AddField(model_name='scraperun', name='source', field=models.CharField(default='arxiv', max_length=32)),
        migrations.RunPython(namespace_existing_arxiv_papers, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name='paper',
            constraint=models.UniqueConstraint(fields=('source', 'source_id'), name='unique_paper_source_id'),
        ),
    ]

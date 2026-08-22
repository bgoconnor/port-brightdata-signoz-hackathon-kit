from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('scraper', '0003_paper_full_text_and_run_kind')]

    operations = [
        migrations.RemoveField(model_name='scraperun', name='paper'),
        migrations.RemoveField(model_name='scraperun', name='kind'),
    ]

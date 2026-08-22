from django.urls import path

from . import views


urlpatterns = [
    path('papers/', views.papers, name='papers'),
    path('papers/<str:arxiv_id>/enrich/', views.enrich_paper, name='enrich-paper'),
    path('scrape-runs/', views.scrape_runs, name='scrape-runs'),
    path(
        'scrape-runs/<int:run_id>/<str:action>/',
        views.scrape_run_action,
        name='scrape-run-action',
    ),
]

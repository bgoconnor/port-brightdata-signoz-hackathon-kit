from django.urls import path

from . import views


urlpatterns = [
    path('summary/', views.summary, name='summary'),
    path('papers/', views.papers, name='papers'),
    path('papers/<path:paper_id>/review/', views.paper_review, name='paper-review'),
    path('papers/<path:paper_id>/', views.paper_detail, name='paper-detail'),
    path('scrape-runs/', views.scrape_runs, name='scrape-runs'),
    path(
        'scrape-runs/<int:run_id>/<str:action>/',
        views.scrape_run_action,
        name='scrape-run-action',
    ),
]

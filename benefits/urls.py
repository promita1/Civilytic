from django.urls import path

from . import api_views

urlpatterns = [
    path("programs/", api_views.ProgramListView.as_view()),
    path("check/", api_views.CheckView.as_view()),
    path("households/<int:pk>/results/", api_views.HouseholdResultsView.as_view()),
]
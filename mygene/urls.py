from django.urls import path
from . import views

urlpatterns = [
    path(
        "gen-treatment-plan/",
        views.process_csv_and_generate_treatment_plan,
        name="gen-treatment-plan",
    ),
    path(
        "",
        views.hello,
        name="root",
    ),
]

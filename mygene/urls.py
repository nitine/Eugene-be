from django.urls import path
from . import views

urlpatterns = [
    path(
        "process-csv/",
        views.process_csv_and_generate_treatment_plan,
        name="gen-treatment-plan",
    ),
    path(
        "get-patients/",
        views.get_patients,
        name="get-patients",
    ),
    path(
        "",
        views.hello,
        name="root",
    ),
]

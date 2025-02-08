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
        views.fetch_all_patients,
        name="patient-list",
    ),
    path(
        "",
        views.hello,
        name="root",
    ),
    path(
        "fetch-chat-history/",
        views.fetch_chat_history,
        name="fetch-chat-history",
    ),
]

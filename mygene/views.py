import requests
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from mygene.models import Patient
from mygene.settings import GEMINI_API_KEY, RUNPOD_ENDPOINT_URL
from django.http import JsonResponse
import requests
import pandas as pd
import io

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# Set up Jinja environment
template_dir = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))

from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from mygene.models import ChatSession, Patient


@csrf_exempt
@require_POST
def process_csv_and_generate_treatment_plan(request):
    """
    Accepts a CSV file, sends it to the Runpod endpoint for disease prediction,
    and generates a treatment plan based on the prediction.
    """
    query = request.POST.get("query", "Comprehensive treatment plan")
    patient_id = request.POST.get("patient_id")

    if not patient_id:
        return JsonResponse({"error": "Patient ID is required."}, status=400)

    if "file" not in request.FILES:
        return JsonResponse({"error": "CSV file is required."}, status=400)

    try:
        csv_file = request.FILES["file"]

        if not csv_file.name.endswith(".csv"):
            return JsonResponse({"error": "File must be a CSV."}, status=400)

        # 🔹 Read file and reset pointer before sending
        file_content = csv_file.read()

        if len(file_content) == 0:
            return JsonResponse({"error": "Uploaded CSV file is empty."}, status=400)

        csv_file.seek(0)  # ✅ Reset file pointer

        files = {
            "file": (csv_file.name, csv_file, "text/csv")
        }  # ✅ Send file object, not read content

        # 🔹 Send to Runpod for prediction
        response = requests.post(
            "https://pangolin-enormous-briefly.ngrok-free.app/predict", files=files
        )

        if response.status_code != 200:
            return JsonResponse(
                {"error": "Error from Runpod", "details": response.text},
                status=response.status_code,
            )

        try:
            prediction_data = response.json()
            disease_prediction = prediction_data.get("prediction")
            disease_info = prediction_data.get("disease_info")

            if not disease_prediction:
                return JsonResponse(
                    {"error": "Disease prediction not found in response."},
                    status=500,
                )

            # 🔹 Generate treatment plan using Gemini
            template = env.get_template("treatmentplan.html.jinja")
            prompt = template.render(Diseases=disease_info)
            gemini_response = model.generate_content(prompt)

            if not gemini_response or not gemini_response.text:
                return JsonResponse(
                    {"error": "Failed to generate treatment plan"}, status=500
                )

            treatment_plan = gemini_response.text

            # 🔹 Save Patient's Query & AI Response
            save_chat_message(patient_id, "patient", query)
            save_chat_message(patient_id, "doctor", treatment_plan)

            return JsonResponse(
                {
                    "success": True,
                    "query": query,
                    "prediction": disease_prediction,
                    "disease": disease_info,
                    "treatment_plan": treatment_plan,
                }
            )

        except Exception as e:
            return JsonResponse(
                {"error": f"Error processing API response: {str(e)}"},
                status=500,
            )

    except Exception as e:
        return JsonResponse({"error": f"Error occurred: {str(e)}"}, status=500)


def save_chat_message(patient_id, sender, message_text):
    """Helper function to store messages in chat history."""
    try:
        patient = Patient.objects.get(id=patient_id)
        chat_session, _ = ChatSession.objects.get_or_create(patient=patient)

        chat_session.messages.append(
            {"sender": sender, "text": message_text, "timestamp": now().isoformat()}
        )
        chat_session.save()
    except Exception as e:
        print(f"Error saving chat message: {e}")  # Log error


def fetch_all_patients(request):
    """
    View function to fetch all patients using the Django ORM.
    Returns a JSON response containing a list of patients.
    """
    try:
        patients = Patient.objects.all()

        patients_list = [
            {
                "id": str(patient.id),
                "name": patient.name,
                "age": patient.age,
                "gender": patient.gender,
                "symptoms": patient.symptoms,
                "is_pending": patient.is_pending,
            }
            for patient in patients
        ]

        return JsonResponse({"status": "success", "patients": patients_list})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@csrf_exempt
def fetch_chat_history(request, patient_id):
    """
    Fetch the chat history for a patient via GET request.
    """
    try:
        chat_session = ChatSession.objects.get(patient_id=patient_id)
        return JsonResponse({"messages": chat_session.messages})
    except ChatSession.DoesNotExist:
        return JsonResponse({"messages": []})


@csrf_exempt
def add_patient(request):
    """
    Add a new patient to the database.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            age = data.get("age")
            gender = data.get("gender")
            symptoms = data.get("symptoms", [])

            if not name or not age or gender not in dict(Patient.GENDER_CHOICES):
                return JsonResponse({"error": "Invalid or missing fields"}, status=400)

            # Create new patient
            patient = Patient.objects.create(
                name=name,
                age=age,
                gender=gender,
                symptoms=symptoms,
            )

            return JsonResponse({"success": True, "patient_id": str(patient.id)})

        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON format"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)


def hello(request):
    return HttpResponse("Hello, world!")

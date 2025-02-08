import os
import json
import requests
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from mygene.settings import GEMINI_API_KEY, RUNPOD_ENDPOINT_URL

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Set up Jinja environment
template_dir = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))


@csrf_exempt
@require_POST
def process_csv_and_generate_treatment_plan(request):
    """
    Accepts a CSV file, sends it to the Runpod endpoint for disease prediction,
    and generates a treatment plan based on the prediction.
    """
    csv_file = request.FILES.get("csv")
    if not csv_file:
        return JsonResponse({"error": "CSV file is required."}, status=400)

    try:
        # Send the CSV file to the Runpod endpoint
        files = {"file": (csv_file.name, csv_file, "text/csv")}
        response = requests.post(RUNPOD_ENDPOINT_URL, files=files)

        if response.status_code == 200:
            try:
                result = response.json()
                disease_prediction = result.get("disease_prediction")
                if not disease_prediction:
                    return JsonResponse(
                        {"error": "Disease prediction not found in response."},
                        status=500,
                    )

                # Generate treatment plan using the disease prediction
                template = env.get_template("treatmentplan.html.jinja")
                prompt = template.render(
                    query="Comprehensive treatment plan", Diseases=disease_prediction
                )
                gemini_response = model.generate_content(prompt)

                if not gemini_response or not gemini_response.text:
                    return JsonResponse(
                        {"error": "Failed to generate treatment plan"}, status=500
                    )

                return JsonResponse(
                    {"success": True, "treatment_plan": gemini_response.text}
                )
            except ValueError:
                return JsonResponse(
                    {"error": "Invalid response format from Runpod."}, status=500
                )
        else:
            return JsonResponse(
                {"error": "Error from Runpod", "details": response.text},
                status=response.status_code,
            )
    except Exception as e:
        return JsonResponse({"error": f"Error occurred: {str(e)}"}, status=500)


def hello(request):
    return HttpResponse("Hello, world!")

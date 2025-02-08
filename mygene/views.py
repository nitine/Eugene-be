import os
import json
import requests
from pathlib import Path
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_GET
import google.generativeai as genai
from jinja2 import Environment, FileSystemLoader
from mygene.settings import GEMINI_API_KEY, RUNPOD_ENDPOINT_URL

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Set up Jinja environment
template_dir = Path(__file__).resolve().parent / "templates"
env = Environment(loader=FileSystemLoader(str(template_dir)))


from django.http import JsonResponse
import requests
import pandas as pd
import io


@csrf_exempt
@require_POST
def process_csv_and_generate_treatment_plan(request):
    """
    Accepts a CSV file, sends it to the Runpod endpoint for disease prediction,
    and generates a treatment plan based on the prediction.
    """
    # Check if file exists in request
    if "file" not in request.FILES:
        return JsonResponse({"error": "CSV file is required."}, status=400)

    try:
        csv_file = request.FILES["file"]

        # Validate file type
        if not csv_file.name.endswith(".csv"):
            return JsonResponse({"error": "File must be a CSV."}, status=400)

        # Read the CSV file content
        try:
            # Read the file content
            file_content = csv_file.read()

            # Prepare the file for upload
            files = {"file": (csv_file.name, file_content, "text/csv")}

            # Send to Runpod endpoint
            response = requests.post(
                "https://pangolin-enormous-briefly.ngrok-free.app/predict", files=files
            )

            if response.status_code == 200:
                try:
                    # Try to parse the response content
                    response_data = response.content.decode("utf-8")

                    # Try to read as CSV if the response is in CSV format
                    try:
                        df = pd.read_csv(io.StringIO(response_data))
                        prediction_data = df.to_dict("records")[
                            0
                        ]  # Get first row as dictionary
                    except:
                        # If not CSV, try JSON
                        prediction_data = response.json()

                    disease_prediction = prediction_data.get("prediction")

                    if not disease_prediction:
                        return JsonResponse(
                            {"error": "Disease prediction not found in response."},
                            status=500,
                        )

                    # Generate treatment plan using the disease prediction
                    template = env.get_template("treatmentplan.html.jinja")
                    prompt = template.render(
                        query="Comprehensive treatment plan",
                        Diseases=disease_prediction,
                    )

                    # Generate content using Gemini
                    gemini_response = model.generate_content(prompt)
                    print(gemini_response)
                    if not gemini_response or not gemini_response.text:
                        return JsonResponse(
                            {"error": "Failed to generate treatment plan"}, status=500
                        )

                    return JsonResponse(
                        {
                            "success": True,
                            "prediction": disease_prediction,
                            "treatment_plan": gemini_response.text,
                        }
                    )

                except Exception as e:
                    return JsonResponse(
                        {
                            "error": f"Error processing response: {str(e)}",
                            "response_content": response_data,
                        },
                        status=500,
                    )
            else:
                return JsonResponse(
                    {
                        "error": "Error from Runpod",
                        "details": response.text,
                        "status_code": response.status_code,
                    },
                    status=response.status_code,
                )

        except Exception as e:
            return JsonResponse(
                {"error": f"Error reading CSV file: {str(e)}"}, status=500
            )

    except Exception as e:
        return JsonResponse({"error": f"Error occurred: {str(e)}"}, status=500)


# @require_GET
# def process_csv_and_generate_treatment_plan(request):
#     """
#     Accepts a GET request, uses a hardcoded CSV file, sends it to the Runpod endpoint for disease prediction,
#     and generates a treatment plan based on the prediction.
#     """
#     # Hardcode the path to your CSV file (update this path as needed)
#     csv_file_path = "/home/nitin/yantra/backend/patients_data/sample_input.csv"

#     try:
#         # Open the CSV file in binary read mode
#         with open(csv_file_path, "rb") as csv_file:
#             # Prepare the file for the POST to Runpod
#             files = {"file": open(csv_file_path, "rb")}
#             response = requests.post(
#                 "https://pangolin-enormous-briefly.ngrok-free.app/predict", files=files
#             )

#         if response.status_code == 200:
#             try:
#                 result = response.json()
#                 disease_prediction = result.get("disease_prediction")
#                 if not disease_prediction:
#                     return JsonResponse(
#                         {"error": "Disease prediction not found in response."},
#                         status=500,
#                     )

#                 # Generate the treatment plan using the disease prediction.
#                 # Here we assume you are using a Jinja2 template to create the prompt.
#                 template = env.get_template("treatmentplan.html.jinja")
#                 prompt = template.render(
#                     query="Comprehensive treatment plan", Diseases=disease_prediction
#                 )

#                 # Generate content with your model
#                 gemini_response = model.generate_content(prompt)
#                 if not gemini_response or not gemini_response.text:
#                     return JsonResponse(
#                         {"error": "Failed to generate treatment plan"}, status=500
#                     )

#                 return JsonResponse(
#                     {"success": True, "treatment_plan": gemini_response.text}
#                 )

#             except ValueError:
#                 return JsonResponse(
#                     {"error": "Invalid response format from Runpod."}, status=500
#                 )
#         else:
#             return JsonResponse(
#                 {"error": "Error from Runpod", "details": response.text},
#                 status=response.status_code,
#             )

#     except Exception as e:
#         return JsonResponse({"error": f"Error occurred: {str(e)}"}, status=500)


def hello(request):
    return HttpResponse("Hello, world!")

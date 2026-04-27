import os
import vertexai
from vertexai.generative_models import GenerativeModel

vertexai.init(
    project=os.getenv("GCP_PROJECT_ID", "gd-gcp-gridu-genai"),
    location=os.getenv("GCP_LOCATION", "us-central1"),
)

MODEL = GenerativeModel("gemini-2.0-flash")

def get_model():
    return MODEL

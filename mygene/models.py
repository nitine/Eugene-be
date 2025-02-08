from django.db import models
import uuid
from django.db.models import (
    JSONField,
)


class Patient(models.Model):
    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    age = models.IntegerField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    symptoms = JSONField(default=list)  # Stores symptoms as a list of strings
    is_pending = models.BooleanField(default=False)  # Tracks pending status

    def __str__(self):
        return self.name


class MedicalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="medical_records"
    )
    diagnosis = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Record for {self.patient.name} - {self.diagnosis}"


class GenomicData(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="genomic_data"
    )
    data = JSONField()

    def __str__(self):
        return f"Genomic Data for {self.patient.name}"


class ChatSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name="chat_sessions"
    )
    messages = JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat Session for {self.patient.name}"

import string

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings
from django.contrib.sessions.models import Session
from datetime import datetime, date, timedelta, time
import random

# -------------------
# Custom User Model
# -----------------
# class User(AbstractUser):
#     ROLE_CHOICES = [
#         ('admin', 'Admin'),
#         ('user', 'User'),
#     ]
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
#     phone_number = models.CharField(max_length=20, blank=True, null=True)
#     email_verified = models.BooleanField(default=False)
#
#     def is_admin(self):
#         return self.role == 'admin'
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email_verified = models.BooleanField(default=False)

    # 🔑 For OTP verification
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_created_at = models.DateTimeField(blank=True, null=True)

    def is_admin(self):
        return self.role == 'admin'

    def generate_otp(self):
        """Generate a 6-digit OTP and save it with timestamp"""
        otp = str(random.randint(string.digits, k=6))  # 6-digit random number
        self.otp = otp
        self.otp_created_at = timezone.now()
        self.save()
        return otp

# -------------------
# Court Model
# -------------------
class Court(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    slot_length = models.PositiveIntegerField(default=60)  # minutes
    location = models.CharField(max_length=200, blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# -------------------
# Booking Model
# -------------------
class Booking(models.Model):
    STATUS_CHOICES = [
        ('booked', 'Booked'),
        ('cancelled', 'Cancelled'),
        ('blocked', 'Blocked'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    court = models.ForeignKey(Court, on_delete=models.CASCADE)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='booked')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('court', 'start_time')  # Prevent double-booking

    def __str__(self):
        return f"{self.court.name} - {self.start_time} by {self.user.username}"

    @staticmethod
    def is_court_available(court, start_time, end_time):
        return not Booking.objects.filter(
            court=court,
            start_time__lt=end_time,
            end_time__gt=start_time,
            status='booked'
        ).exists()


# -------------------
# CourtSlot Model
# -------------------
class CourtSlot(models.Model):
    court = models.ForeignKey(Court, on_delete=models.CASCADE, related_name='slots')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)

    booked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="booked_slots"
    )

    class Meta:
        unique_together = ('court', 'date', 'start_time')
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.court.name} - {self.date} {self.start_time} to {self.end_time}"


# -------------------
# Member Model
# -------------------
class Member(models.Model):
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=50, default="Regular")
    created_at = models.DateTimeField(auto_now_add=True)
    added_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="added_members"
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


# -------------------
# Proxy Model for Export
# -------------------
class ExportMembers(Member):
    class Meta:
        proxy = True
        verbose_name = "Export Members"
        verbose_name_plural = "Export Members"


# -------------------
# Excel Upload
# -------------------
class ExcelUpload(models.Model):
    file = models.FileField(upload_to="uploads/excel/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Excel File ({self.uploaded_at:%Y-%m-%d %H:%M})"


# -------------------
# Session Management
# -------------------
def terminate_other_sessions(user, current_session_key):
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id) and session.session_key != current_session_key:
            session.delete()

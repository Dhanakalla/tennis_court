# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from .models import User
#
# class RegisterForm(UserCreationForm):
#     class Meta:
#         model = User
#         fields = ['username', 'email', 'password1', 'password2', 'role']
#
# from django import forms
# from .models import Court, Booking
# from django.utils import timezone
# from datetime import timedelta
#
# class CourtForm(forms.ModelForm):
#     class Meta:
#         model = Court
#         fields = ['name', 'description', 'slot_length']
#
#
# class BookingForm(forms.ModelForm):
#     class Meta:
#         model = Booking
#         fields = ['court', 'start_time']
#
#     def clean(self):
#         cleaned_data = super().clean()
#         start_time = cleaned_data.get('start_time')
#         court = cleaned_data.get('court')
#
#         if start_time and start_time < timezone.now():
#             raise forms.ValidationError("You cannot book a slot in the past.")
#
#         if court and start_time:
#             if Booking.objects.filter(court=court, start_time=start_time, status='booked').exists():
#                 raise forms.ValidationError("This slot is already booked.")
#         return cleaned_data
#
#     def save(self, commit=True):
#         booking = super().save(commit=False)
#         booking.end_time = booking.start_time + timedelta(minutes=booking.court.slot_length)
#         if commit:
#             booking.save()
#         return booking


from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelformset_factory
from django.utils import timezone
from datetime import timedelta
from .models import User, Court, Booking


# -------------------
# User Registration Form
# -------------------

User = get_user_model()
class RegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


# -------------------
# Court Form (Admin/Staff Use)
# -------------------
class CourtForm(forms.ModelForm):
    class Meta:
        model = Court
        fields = ['name', 'description', 'slot_length', 'location', 'is_available']


# -------------------
# Booking Form
# -------------------
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['court', 'start_time']

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        court = cleaned_data.get('court')

        # Prevent booking in the past
        if start_time and start_time < timezone.now():
            raise forms.ValidationError("You cannot book a slot in the past.")

        # Prevent overlapping bookings
        if court and start_time:
            end_time = start_time + timedelta(minutes=court.slot_length)
            if not Booking.is_court_available(court, start_time, end_time):
                raise forms.ValidationError("This slot is already booked.")

        return cleaned_data

    def save(self, commit=True, user=None):
        booking = super().save(commit=False)
        booking.end_time = booking.start_time + timedelta(minutes=booking.court.slot_length)

        # Assign the user automatically if provided
        if user:
            booking.user = user

        if commit:
            booking.save()
        return booking

# from django import forms
# from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User
# User = get_user_model()
# class UserRegisterForm(UserCreationForm):
#     email = forms.EmailField(required=True)
#
#     class Meta:
#         model = User
#         fields = ["username", "email", "password1", "password2"]

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserRegisterForm(UserCreationForm):
    class Meta:
        model = User
        fields = ["email", "phone_number", "password1", "password2"]



from django import forms

class ExportMembersForm(forms.Form):
    from_date = forms.DateField(
        label="From date",
        widget=forms.DateInput(attrs={"type": "date"})
    )
    to_date = forms.DateField(
        label="To date",
        widget=forms.DateInput(attrs={"type": "date"})
    )






# forms.py
from django import forms

class UploadExcelForm(forms.Form):
    excel_file = forms.FileField(label="Choose Excel File")

from django import forms
from .models import Member   # make sure you have a Member model

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = "__all__"   # or specify the fields like ["name", "email", "phone"]



from django import forms
from django.forms import modelformset_factory
from .models import CourtSlot

class CourtSlotForm(forms.ModelForm):
    class Meta:
        model = CourtSlot
        fields = ["court", "date", "start_time", "end_time", "is_booked"]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
        }

CourtSlotFormSet = modelformset_factory(
    CourtSlot,
    form=CourtSlotForm,
    extra=3,       # show 3 empty rows
    can_delete=True
)


# core/forms.py
from django import forms
from .models import Court
from datetime import time

def generate_hourly_choices():
    choices = []
    for hour in range(24):
        start = time(hour, 0)
        end = time((hour + 1) % 24, 0)
        choices.append((f"{start.strftime('%H:%M')}-{end.strftime('%H:%M')}",
                        f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"))
    return choices

class BulkSlotForm(forms.Form):
    court = forms.ModelChoiceField(queryset=Court.objects.all())
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    slots = forms.MultipleChoiceField(
        choices=generate_hourly_choices(),
        widget=forms.CheckboxSelectMultiple,
        help_text="Select the hours you want to generate slots for"
    )


import pandas as pd
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib.sessions.models import Session
from datetime import datetime, date, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import CourtSlot, Booking

from .forms import (
    UserRegisterForm,
    CourtForm,
    BookingForm,
    UploadExcelForm,
    MemberForm,
)
from .models import Court, Booking, CourtSlot, Member, terminate_other_sessions

User = get_user_model()

# -----------------------
# Custom Decorator
# -----------------------
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.role != "admin":
            return HttpResponseForbidden("Not allowed")
        return view_func(request, *args, **kwargs)
    return wrapper

# -----------------------
# Authentication Views
# -----------------------
User = get_user_model()

def register_view(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Auto-login after register
            return redirect("dashboard")
    else:
        form = UserRegisterForm()
    return render(request, "register.html", {"form": form})





def logout_view(request):
    logout(request)
    return redirect("login")

# -----------------------
# Dashboard
# -----------------------

from django.contrib.auth.decorators import login_required

# @login_required(login_url="login")
# def dashboard(request):
#     if request.user.is_superuser or request.user.role == "admin":
#         # Admin Dashboard
#         context = {
#             "users": User.objects.all(),
#             "courts": Court.objects.all(),
#             "bookings": Booking.objects.select_related("user", "court").order_by("-created_at")[:5],  # recent 5 bookings
#             "verified_users": User.objects.filter(is_active=True).count(),
#             "unverified_users": User.objects.filter(is_active=False).count(),
#             "total_courts": Court.objects.count(),
#             "total_members": User.objects.filter(role="user").count(),
#             "total_bookings": Booking.objects.count(),
#             "total_slots": CourtSlot.objects.count(),
#             "booked_slots": CourtSlot.objects.filter(is_booked=True).count(),
#             "remaining_slots": CourtSlot.objects.filter(is_booked=False).count(),
#             "recent_bookings": recent_bookings,
#         }
#         return render(request, "admin_dashboard.html", context)
#
#     else:
#         # User Dashboard
#         context = {
#             "my_bookings": Booking.objects.filter(user=request.user).select_related("court").order_by("-created_at"),
#             "profile": request.user,
#         }
#         return render(request, "user_dashboard.html", context)
# # -----------------------


@login_required
def dashboard(request):
    if request.user.is_superuser or request.user.role == "admin":
        # ✅ Define recent_bookings here
        recent_bookings = Booking.objects.select_related("user", "court").order_by("-start_time")[:5]

        context = {
            "total_courts": Court.objects.count(),
            "total_slots": CourtSlot.objects.count(),
            "total_members": User.objects.filter(role="user").count(),
            "total_bookings": Booking.objects.count(),
            "booked_slots": CourtSlot.objects.filter(is_booked=True).count(),
            "remaining_slots": CourtSlot.objects.filter(is_booked=False).count(),
            "recent_bookings": recent_bookings,  # ✅ now this exists
        }
        return render(request, "admin_dashboard.html", context)

    else:
        # User Dashboard
        context = {
            "my_bookings": Booking.objects.filter(user=request.user).select_related("court").order_by("-created_at"),
            "profile": request.user,
        }
        return render(request, "user_dashboard.html", context)




# Courts & Bookings
# -----------------------
@login_required
def add_court(request):
    if request.method == "POST":
        form = CourtForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Court added successfully!")
            return redirect("dashboard")
    else:
        form = CourtForm()
    return render(request, "add_court.html", {"form": form})



from django.contrib import messages
from django.shortcuts import redirect, render
from django.utils import timezone
from datetime import date, timedelta, datetime
from .models import CourtSlot, Booking

def book_court(request):
    today = date.today()
    next_7_days = [today + timedelta(days=i) for i in range(7)]

    # Get selected date from query parameters
    selected_date_str = request.GET.get("date")
    selected_date = date.fromisoformat(selected_date_str) if selected_date_str else today

    # Fetch available slots for that day
    slots = CourtSlot.objects.filter(date=selected_date).order_by("court", "start_time")

    if request.method == "POST":
        slot_id = request.POST.get("slot_id")
        try:
            slot = CourtSlot.objects.get(id=slot_id, is_booked=False)
        except CourtSlot.DoesNotExist:
            messages.error(request, "That slot is no longer available.")
            return redirect("core:book_court")  # Stay on booking page

        # Combine date and time safely and make timezone aware
        start_time = timezone.make_aware(datetime.combine(slot.date, slot.start_time))
        end_time = timezone.make_aware(datetime.combine(slot.date, slot.end_time))

        # Create booking
        Booking.objects.create(
            user=request.user,
            court=slot.court,
            start_time=start_time,
            end_time=end_time,
            status="booked",
        )

        # Update slot to mark it booked
        slot.is_booked = True
        slot.booked_by = request.user
        slot.save()

        # ✅ Success popup message
        messages.success(request, "Court booked successfully!")

        return redirect("core:book_court")  # Redirect back to same booking page

    return render(request, "book_court.html", {
        "slots": slots,
        "next_7_days": next_7_days,
        "selected_date": selected_date,
    })



# @login_required
# def booking_history(request):
#     bookings = Booking.objects.filter(user=request.user).order_by("-start_time")
#     return render(request, "booking_history.html", {"bookings": bookings})
@login_required
def booking_history(request):
    if request.user.is_superuser or request.user.role == "admin":
        # Admin sees all bookings
        bookings = Booking.objects.all().order_by('-start_time')
    else:
        # User sees only their own
        bookings = Booking.objects.filter(user=request.user).order_by('-start_time')

    return render(request, "booking_history.html", {"bookings": bookings})


@login_required
def cancel_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    booking.status = "cancelled"
    booking.save()
    messages.success(request, "Booking cancelled successfully.")
    return redirect("dashboard")



from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .forms import MemberForm
from .models import User

# Show all members
@login_required
def view_members(request):
    members = Member.objects.filter(added_by=request.user).order_by("-id")
    return render(request, "members/view_members.html", {"members": members})

# Add member (user-facing)
@login_required
def add_member(request):
    if request.method == "POST":
        form = MemberForm(request.POST)
        if form.is_valid():
            member = form.save(commit=False)
            member.added_by = request.user
            member.save()
            return redirect("core:view_members")
    else:
        form = MemberForm()
    return render(request, "members/add_member.html", {"form": form})





@login_required
@admin_required
def edit_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    if request.method == "POST":
        form = MemberForm(request.POST, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, "Member updated!")
            return redirect("view_members")
    else:
        form = MemberForm(instance=member)
    return render(request, "edit_member.html", {"form": form})


@login_required
@admin_required
def delete_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    member.delete()
    messages.success(request, "Member deleted.")
    return redirect("view_members")


# -----------------------
# Import Members from Excel
# -----------------------
@login_required
def import_excel(request):
    if request.method == "POST":
        form = UploadExcelForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES["excel_file"]
            df = pd.read_excel(excel_file).fillna("")

            admin_user = User.objects.filter(is_superuser=True).first()

            for _, row in df.iterrows():
                Member.objects.create(
                    first_name=row.get("first_name", "").strip(),
                    last_name=row.get("last_name", "").strip(),
                    email=row.get("email", "").strip(),
                    phone_number=row.get("phone_number", "").strip(),
                    added_by=admin_user,
                )
            messages.success(request, "Members imported successfully!")
            return redirect("view_members")
    else:
        form = UploadExcelForm()

    return render(request, "import_members.html", {"form": form})



# -----------------------
# Admin Custom LoginView (Remember Me + Terminate Other Sessions)
# -----------------------
from django.contrib.auth.views import LoginView

class CustomLoginView(LoginView):
    template_name = "login.html"

    def form_valid(self, form):
        remember_me = self.request.POST.get("remember_me")
        login(self.request, form.get_user())

        # Set session expiry
        if remember_me:
            self.request.session.set_expiry(1209600)  # 2 weeks
        else:
            self.request.session.set_expiry(0)  # browser close

        # Terminate other sessions safely
        terminate_other_sessions(self.request.user, self.request.session.session_key)

        return redirect("dashboard")



from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Already logged in

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        remember_me = request.POST.get("remember_me") == "on"

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)

            # Handle remember me
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)        # close browser

            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "login.html")




from django.http import HttpResponse


def session_info(request):
    expiry_age = request.session.get_expiry_age()     # in seconds
    expiry_date = request.session.get_expiry_date()   # datetime
    return HttpResponse(
        f"""
        <h2>Session Debug Info</h2>
        <p><b>User:</b> {request.user}</p>
        <p><b>Expiry age:</b> {expiry_age} seconds</p>
        <p><b>Expiry date:</b> {expiry_date}</p>
        """
    )



import csv
from django.http import HttpResponse
from django.shortcuts import render
from .forms import ExportMembersForm
from .models import Member

def export_members(request):
    if request.method == "POST":
        form = ExportMembersForm(request.POST)
        if form.is_valid():
            from_date = form.cleaned_data["from_date"]
            to_date = form.cleaned_data["to_date"]

            response = HttpResponse(content_type="text/csv")
            response['Content-Disposition'] = 'attachment; filename="members.csv"'

            writer = csv.writer(response)
            writer.writerow(["ID", "Name", "Email", "Phone", "Joined Date", "Status"])

            members = Member.objects.filter(
                created_at__date__range=[from_date, to_date]
            )

            for member in members:
                writer.writerow([
                    member.id,
                    f"{member.first_name} {member.last_name}",
                    member.email,
                    member.phone_number,
                    member.created_at.strftime("%Y-%m-%d"),
                ])

            return response
    else:
        form = ExportMembersForm()

    return render(request, "admin/export_members.html", {"form": form})




# def view_court_slots(request):
#     slots = CourtSlot.objects.select_related("court").all().order_by("court__name", "start_time")
#     return render(request, "view_court_slots.html", {"slots": slots})

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import CourtSlot

def view_court_slots(request):
    slots = CourtSlot.objects.all().order_by("date", "start_time")

    if request.method == "POST":
        slot_id = request.POST.get("slot_id")
        action = request.POST.get("action")
        slot = get_object_or_404(CourtSlot, id=slot_id)

        if action == "block":
            slot.is_blocked = True
            slot.save()
            messages.success(request, "Slot blocked successfully!")
        elif action == "unblock":
            slot.is_blocked = False
            slot.save()
            messages.success(request, "Slot unblocked successfully!")
            return redirect("/view_court_slots/")

    return render(request, "view_court_slots.html", {"slots": slots})

from django.shortcuts import render

def book_slot(request):
    return render(request, "book_slot.html")




from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import CourtSlotFormSet
from .models import CourtSlot

def add_court_slot(request):
    if request.method == "POST":
        formset = CourtSlotFormSet(request.POST, queryset=CourtSlot.objects.none())
        if formset.is_valid():
            formset.save()
            messages.success(request, "Court slots added successfully!")
            # ✅ Use namespace if needed
            try:
                return redirect("core:add_court_slot")  # if you included urls with namespace="core"
            except:
                return redirect("add_court_slot")  # fallback if no namespace
        else:
            messages.error(request, "There was an error. Please check the form.")
    else:
        formset = CourtSlotFormSet(queryset=CourtSlot.objects.none())

    return render(request, "add_court_slot.html", {"formset": formset})



# core/views.py
from datetime import datetime, timedelta
from .forms import BulkSlotForm
from .models import CourtSlot

def bulk_create_slots(request):
    if request.method == "POST":
        form = BulkSlotForm(request.POST)
        if form.is_valid():
            court = form.cleaned_data["court"]
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]
            selected_slots = form.cleaned_data["slots"]

            created_count = 0
            current_date = start_date
            while current_date <= end_date:
                for slot in selected_slots:
                    start_str, end_str = slot.split("-")
                    start_time = datetime.strptime(start_str, "%H:%M").time()
                    end_time = datetime.strptime(end_str, "%H:%M").time()

                    if not CourtSlot.objects.filter(
                        court=court, date=current_date, start_time=start_time
                    ).exists():
                        CourtSlot.objects.create(
                            court=court,
                            date=current_date,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        created_count += 1

                current_date += timedelta(days=1)

            messages.success(request, f"{created_count} slots created successfully!")
            return redirect("core:view_court_slots")  # Change as needed
    else:
        form = BulkSlotForm()

    return render(request, "bulk_create_slots.html", {"form": form})

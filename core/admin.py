# from sys import path
#
# from django.contrib import admin
# from django.contrib.auth import get_user_model
# from django.http import HttpResponse
# from django.shortcuts import render
# from django.utils import timezone
# from datetime import datetime, timedelta, time as dtime
#
# from .forms import ExportMembersForm
# from .models import Court, CourtSlot, Booking, User, ExcelUpload
#
#
# @admin.action(description="Generate slots for next 7 days (8am–8pm)")
# def generate_week_slots(modeladmin, request, queryset):
#     for court in queryset:
#         for day in range(7):
#             date = timezone.localdate() + timedelta(days=day)
#             start = dtime(8, 0)
#             end   = dtime(20, 0)
#             cur = datetime.combine(date, start)
#             end_dt = datetime.combine(date, end)
#             while cur < end_dt:
#                 nxt = cur + timedelta(minutes=court.slot_length or 60)
#                 CourtSlot.objects.get_or_create(
#                     court=court,
#                     date=date,
#                     start_time=cur.time(),
#                     end_time=nxt.time(),
#                 )
#                 cur = nxt
#
# @admin.register(Court)
# class CourtAdmin(admin.ModelAdmin):
#     list_display = ("name", "location", "is_available")
#     actions = [generate_week_slots]
#
# @admin.register(CourtSlot)
# class CourtSlotAdmin(admin.ModelAdmin):
#     list_display = ("court", "date", "start_time", "end_time", "is_booked", "get_booked_by")
#
#     def get_booked_by(self, obj):
#         return obj.booked_by.username if obj.booked_by else "-"
#     get_booked_by.short_description = "Booked By"
#
# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     list_display = ("user", "court", "start_time", "end_time", "status")
#     list_filter = ("court", "status", "start_time")
#     search_fields = ("user__username", "court__name")
#
# from django.apps import AppConfig
#
# class TennisCourtConfig(AppConfig):
#     default_auto_field = "django.db.models.BigAutoField"
#     name = "tennis_court"
#
#     def ready(self):
#         from . import tasks
#         tasks.start()
#
#
#
#
# # admin.py
# from django.contrib import admin
# from django.urls import path
# from django.http import HttpResponse
# from django.shortcuts import render
# import pandas as pd
# from .models import Member, ExportMembers
# from .forms import ExportMembersForm
#
#
# @admin.register(ExportMembers)
# class ExportMembersAdmin(admin.ModelAdmin):
#     """Admin page for exporting members"""
#
#     def has_add_permission(self, request):
#         return False
#     def has_change_permission(self, request, obj=None):
#         return False
#     def has_delete_permission(self, request, obj=None):
#         return False
#
#     def get_urls(self):
#         urls = super().get_urls()
#         custom_urls = [
#             path("", self.admin_site.admin_view(self.export_members), name="export-members"),
#         ]
#         return custom_urls + urls
#
#     def export_members(self, request):
#         if request.method == "POST":
#             form = ExportMembersForm(request.POST)
#             if form.is_valid():
#                 from_date = form.cleaned_data["from_date"]
#                 to_date = form.cleaned_data["to_date"]
#
#                 qs = Member.objects.filter(
#                     created_at__date__range=(from_date, to_date)
#                 ).values(
#                     "first_name", "last_name", "email",
#                     "phone_number", "added_by__username", "created_at"
#                 )
#
#                 df = pd.DataFrame(list(qs))
#                 if "created_at" in df.columns:
#                     df["created_at"] = pd.to_datetime(df["created_at"]).dt.tz_localize(None)
#
#                 response = HttpResponse(
#                     content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
#                 )
#                 response["Content-Disposition"] = f'attachment; filename="members_{from_date}_to_{to_date}.xlsx"'
#                 df.to_excel(response, index=False)
#                 return response
#         else:
#             form = ExportMembersForm()
#
#         context = {
#             **self.admin_site.each_context(request),
#             "form": form,
#             "opts": self.model._meta,
#             "title": "Export Members Report",
#         }
#         return render(request, "admin/export_members.html", context)
#
#
#
#
#
# @admin.register(ExcelUpload)
# class ExcelUploadAdmin(admin.ModelAdmin):
#     list_display = ("file", "uploaded_at")
#
#     def save_model(self, request, obj, form, change):
#         super().save_model(request, obj, form, change)
#
#         excel_file = obj.file.path
#         df = pd.read_excel(excel_file)
#
#         # Normalize headers to lowercase
#         df.columns = df.columns.str.lower()
#         df = df.fillna('')
#
#         admin_user = User.objects.filter(is_superuser=True).first()
#
#         for _, row in df.iterrows():
#             first_name = str(row.get('first_name', '')).strip()
#             last_name = str(row.get('last_name', '')).strip()
#             email = str(row.get('email', '')).strip()
#             phone_number = str(row.get('phone_number', '')).strip() or str(row.get('phone', '')).strip()
#
#             if first_name:
#                 Member.objects.create(
#                     first_name=first_name,
#                     last_name=last_name,
#                     email=email,
#                     phone_number=phone_number,
#                     added_by=admin_user
#                 )
#
#
# from django.contrib import admin
# from .models import Member
#
# @admin.register(Member)
# class MemberAdmin(admin.ModelAdmin):
#     list_display = ('first_name', 'last_name', 'email', 'phone_number', 'added_by', 'created_at')
#     search_fields = ('first_name', 'last_name', 'email')





from django.urls import path
from . import views

app_name="core"

urlpatterns = [
    # ------------------------
    # Dashboard (shared)
    # ------------------------
    path("dashboard/", views.dashboard, name="dashboard"),

    # ------------------------
    # Authentication
    # ------------------------
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("register/", views.register_view, name="register"),
    path("session-info/", views.session_info, name="session_info"),

    # ------------------------
    # Courts
    # ------------------------
    path("courts/add/", views.add_court, name="add_court"),
    # path("courts/", views.view_courts, name="view_courts"),
    path("add-court-slot/", views.add_court_slot, name="add_court_slot"),
    # path("view/court/slots/", views.view_court_slots, name="view_court_slots"),
    path("view_court_slots/", views.view_court_slots, name="view_court_slots"),
    path("bulk_create_slots/", views.bulk_create_slots, name="bulk_create_slots"),
    # ------------------------
    # Bookings
    # ------------------------
    path("book/court/", views.book_court, name="book_court"),
    path('booking/history/', views.booking_history, name='booking_history'),
    # path("booking/history/", views.booking_history, name="booking_history"),  # ✅ Added

    # ------------------------
    # Members (User side)
    # ------------------------
    path("members/add/", views.add_member, name="add_member"),
    path("members/view/", views.view_members, name="view_members"),

    # ------------------------
    # Members (Admin side)
    # ------------------------
    # path("admin/members/add/", views.add_member_admin, name="add_member_admin"),
    # path("members/view/", views.view_members, name="view_members"),
    path("admin/members/import/", views.import_excel, name="import_members"),
    path("admin/members/export/", views.export_members, name="export_members"),
    path("admin/members/edit/<int:member_id>/", views.edit_member, name="edit_member"),
    path("admin/members/delete/<int:member_id>/", views.delete_member, name="delete_member"),
]

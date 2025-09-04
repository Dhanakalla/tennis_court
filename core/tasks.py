# # tennis_court/tasks.py
# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore
# from .models import Court
#
# def start():
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(), "default")
#
#     # Run daily at midnight
#     scheduler.add_job(
#         auto_generate_slots,
#         "cron",
#         hour=0,
#         minute=0,
#         id="slot_generator",
#         replace_existing=True,
#     )
#
#     scheduler.start()
#
# def auto_generate_slots():
#     for court in Court.objects.all():
#         court.create_weekly_slots()
#
#
# from datetime import timedelta, time
# from django.utils import timezone
# from core.models import Slot, Court  # make sure models are correct
#
# def generate_weekly_slots():
#     today = timezone.now().date()
#     days_to_generate = 7  # one week
#
#     # Define 8 fixed slots
#     slot_times = [
#         (time(6, 0), time(7, 0)),
#         (time(7, 0), time(8, 0)),
#         (time(8, 0), time(9, 0)),
#         (time(9, 0), time(10, 0)),
#         (time(16, 0), time(17, 0)),
#         (time(17, 0), time(18, 0)),
#         (time(18, 0), time(19, 0)),
#         (time(19, 0), time(20, 0)),
#     ]
#
#     courts = Court.objects.all()
#
#     for i in range(days_to_generate):
#         date = today + timedelta(days=i)
#         for court in courts:
#             for start, end in slot_times:
#                 Slot.objects.get_or_create(
#                     court=court,
#                     date=date,
#                     start_time=start,
#                     end_time=end
#                 )
# from apscheduler.schedulers.background import BackgroundScheduler
# from django_apscheduler.jobstores import DjangoJobStore
# from core.tasks import generate_weekly_slots
#
# def start():
#     scheduler = BackgroundScheduler()
#     scheduler.add_jobstore(DjangoJobStore(), "default")
#
#     # Run every Sunday at midnight
#     scheduler.add_job(
#         generate_weekly_slots,
#         trigger="cron",
#         day_of_week="sun",
#         hour=0,
#         minute=0,
#         id="weekly_slot_job",
#         replace_existing=True,
#     )
#
#     scheduler.start()

from datetime import timedelta, time
from django.utils import timezone
from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore

from core.models import Court, Slot


# -------------------------
# TASKS
# -------------------------

def auto_generate_slots():
    """Call model method to generate slots daily."""
    for court in Court.objects.all():
        if hasattr(court, "create_weekly_slots"):
            court.create_weekly_slots()


def generate_weekly_slots():
    """Generate fixed slots for the next 7 days for all courts."""
    today = timezone.now().date()
    days_to_generate = 7  # one week

    # Define 8 fixed slots
    slot_times = [
        (time(6, 0), time(7, 0)),
        (time(7, 0), time(8, 0)),
        (time(8, 0), time(9, 0)),
        (time(9, 0), time(10, 0)),
        (time(16, 0), time(17, 0)),
        (time(17, 0), time(18, 0)),
        (time(18, 0), time(19, 0)),
        (time(19, 0), time(20, 0)),
    ]

    courts = Court.objects.all()
    for i in range(days_to_generate):
        date = today + timedelta(days=i)
        for court in courts:
            for start, end in slot_times:
                Slot.objects.get_or_create(
                    court=court,
                    date=date,
                    start_time=start,
                    end_time=end
                )


# -------------------------
# SCHEDULER SETUP
# -------------------------

def start():
    """Start background scheduler for periodic jobs."""
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    # Run daily at midnight
    scheduler.add_job(
        auto_generate_slots,
        trigger="cron",
        hour=0,
        minute=0,
        id="daily_slot_generator",
        replace_existing=True,
    )

    # Run every Sunday at midnight
    scheduler.add_job(
        generate_weekly_slots,
        trigger="cron",
        day_of_week="sun",
        hour=0,
        minute=0,
        id="weekly_slot_job",
        replace_existing=True,
    )

    scheduler.start()

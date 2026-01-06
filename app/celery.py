"""
celery worker configuration
"""

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

# Create a Celery APP instance
cel_app = Celery("celery_app")

# Use environment variable for Docker compatibility, fallback to localhost for local development
redis_url = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")

cel_app.conf.broker_url = redis_url
cel_app.conf.result_backend = redis_url
cel_app.conf.result_backend_transport_options = {"retry_policy": {"timeout": 5.0}}

# Load settings from Django settings file (use a CELERY_ prefix)
cel_app.config_from_object("django.conf.settings")

# Auto discover tasks from all registered Django configs
cel_app.autodiscover_tasks()

# cel_app.conf.beat_schedule = {
#     'add-every-30-seconds': {
#         'task': 'customer.tasks.add',
#         'schedule': 30.0,
#         'args': (random.randint(1,10), random.randint(11,30))
#     },
# #     # Monthly tasks
# #    'generate-bills-monthly': {
# #        'task': 'customer.tasks.generate_customer_bills',
# #        'schedule': crontab(minute=0, hour=0, day_of_month=1),
# #    },
# #    # Again start for missing bills
# #    'generate-bills-monthly': {
# #        'task': 'customer.tasks.generate_customer_bills',
# #        'schedule': crontab(minute=0, hour=3, day_of_month=1),
# #    },
# #    'deactivate-customers-monthly': {
# #        'task': 'customer.tasks.deactivate_due_payment_customers',
# #        'schedule': crontab(minute=0, hour=0, day_of_month=10),
# #    },
# #    # Again start for check again
# #    'deactivate-customers-monthly': {
# #        'task': 'customer.tasks.deactivate_due_payment_customers',
# #        'schedule': crontab(minute=0, hour=6, day_of_month=10),
# #    },
# }
cel_app.conf.timezone = "Asia/Dhaka"


@cel_app.task(bind=True)
def debug_task(self):
    """debug celery task"""
    print(f"Request: {self.request!r}")

import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'eliminar-tickets-expirados-cada-5-min': {
        'task': 'payment.tasks.eliminar_tickets_expirados',
        'schedule': crontab(minute='*/5'),
    },
    'evento-finalizado-cada-5-min': {
        'task': 'products.tasks.evento_finalizado',
        'schedule': crontab(minute='*/5'),
    },
}

app.conf.task_default_queue = 'default'

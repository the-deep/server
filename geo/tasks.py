from celery import shared_task


@shared_task
def test(x, y):
    return x + y

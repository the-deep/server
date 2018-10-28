import traceback
import logging

from celery import shared_task
from redis_store import redis
from django.db import transaction

from .models import Book, Field, Sheet
from .extractor import csv


logger = logging.getLogger(__name__)


def _tabular_extract_book(book):
    if book.file_type == Book.CSV:
        csv.extract(book)
    auto_detect_and_update_fields(book)
    return True


def auto_detect_and_update_fields(book):
    for sheet in book.sheet_set.all():
        data = sheet.data

        field_ids = data[0].keys() if data else []
        field_ids = [x for x in field_ids if x.isnumeric()]  # omit non numeric
        fields = Field.objects.filter(id__in=field_ids)

        fields_default_types = {x.id: x.type for x in fields}
        fields_current_types = {x.id: None for x in fields}
        fields_set_default = {x.id: False for x in fields}

        for row in data:
            for k, v in row.items():
                type = Field.STRING
                if parse_number(v):
                    type = Field.NUMBER
                # elif parse_date(v):
                #     type = Field.DATE
                else:
                    type = Field.STRING

                curr_type = fields_current_types.get(k)

                if not k.isnumeric():  # because k is the pk of field
                    continue
                key = int(k)
                # no need to check further if the field has default type
                if fields_set_default.get(key) is True:
                    continue
                if curr_type is not None and curr_type != type:
                    # mixed types present, set original type
                    fields_set_default[key] = True
                    fields_current_types[key] = fields_default_types.get(k) \
                        or Field.STRING
                elif curr_type is None:
                    fields_current_types[key] = type

        for field in fields:
            field.type = fields_current_types.get(field.id, Field.STRING)
            field.save()


def parse_number(val):
    try:
        float(val)
        return True
    except ValueError as ve:
        return False


@shared_task
def tabular_extract_book(book_id):
    key = 'tabular_file_extraction_{}'.format(book_id)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    book = Book.objects.get(id=book_id)
    try:
        with transaction.atomic():
            return_value = _tabular_extract_book(book)
        book.status = Book.SUCCESS
    except Exception:
        logger.error(traceback.format_exc())
        book.status = Book.FAILED
        book.error = Book.UNKNOWN_ERROR  # TODO: handle all type of error
        return_value = False

    book.save()

    lock.release()
    return return_value

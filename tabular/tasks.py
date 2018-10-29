import traceback
import logging

from celery import shared_task
from redis_store import redis
from django.db import transaction
from django.contrib.postgres import search

from geo.models import GeoArea

from .models import Book, Field, Geodata
from .extractor import csv, xlsx
from .utils import (
    parse_number,
    parse_datetime,
    parse_geo,
    get_geos_dict,
)


logger = logging.getLogger(__name__)


def _tabular_extract_book(book):
    if book.file_type == Book.CSV:
        csv.extract(book)
    if book.file_type == Book.XLSX:
        xlsx.extract(book)
    auto_detect_and_update_fields(book)
    return True


def _tabular_meta_extract_book(book):
    if book.file_type == Book.XLSX:
        xlsx.extract_meta(book)
    return True


def auto_detect_and_update_fields(book):
    # get geos first
    geos = get_geos_dict(book.project)

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
                elif parse_datetime(v):
                    type = Field.DATETIME
                elif parse_geo(v, geos):
                    type = Field.GEO
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


def _tabular_meta_extract_geo(geodata):
    field = geodata.field
    project = field.sheet.book.project
    project_geoareas = GeoArea.objects.filter(
        admin_level__region__project=project
    )
    geodata_data = []
    for row in geodata.field.sheet.data:
        similar_areas = []
        query = row.get(field.pk)
        geoareas = project_geoareas.annotate(
            similarity=search.TrigramSimilarity('title', query),
        ).filter(similarity__gt=0.4).order_by('-similarity')
        for geoarea in geoareas:
            similar_areas.append({
                'id': geoarea.pk,
                'similarity': geoarea.similarity,
            })
        geodata_data.append({
            'similar_areas': similar_areas,
            'selected_id': geoareas.first().pk if geoareas.exists() else None,
        })
    geodata.data = geodata_data
    geodata.save()
    return True


@shared_task
def tabular_extract_book(book_pk):
    key = 'tabular_extract_book_{}'.format(book_pk)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    book = Book.objects.get(pk=book_pk)
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


@shared_task
def tabular_meta_extract_book(book_pk):
    key = 'tabular_meta_extract_book_{}'.format(book_pk)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    book = Book.objects.get(pk=book_pk)
    try:
        with transaction.atomic():
            return_value = _tabular_meta_extract_book(book)
        book.meta_status = Book.SUCCESS
    except Exception:
        logger.error(traceback.format_exc())
        book.meta_status = Book.FAILED
        book.error = Book.UNKNOWN_ERROR  # TODO: handle all type of error
        return_value = False

    book.save()

    lock.release()
    return return_value


@shared_task
def tabular_extract_geo(geodata_pk):
    key = 'tabular_meta_extract_geo_{}'.format(geodata_pk)
    lock = redis.get_lock(key, 60 * 60 * 24)  # Lock lifetime 24 hours
    have_lock = lock.acquire(blocking=False)
    if not have_lock:
        return False

    geodata = Geodata.objects.get(pk=geodata_pk)
    try:
        with transaction.atomic():
            return_value = _tabular_meta_extract_geo(geodata)
        geodata.status = Geodata.SUCCESS
    except Exception:
        logger.error(traceback.format_exc())
        geodata.status = Geodata.FAILED
        return_value = False

    geodata.save()

    lock.release()
    return return_value

import traceback
import logging
import math

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

AUTO_DETECT_THRESHOLD = 0.8
# Means, 80% of entries in a column should be of same type in order for column
# to be of that type


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
    # get geos indexed by title first
    geos_names = get_geos_dict(book.project)
    # Index by codes, we need to search by codes as well
    geos_codes = {v['code'].lower(): v for k, v in geos_names.items()}

    for sheet in book.sheet_set.all():
        data = sheet.data or []

        field_ids = [
            x for x in data[0].keys() if x.isnumeric()
        ] if data else []
        fields = Field.objects.filter(id__in=field_ids)

        fields_types_count = {x.id: {} for x in fields}
        geo_counts = {
            x.id: {
                'geo_types': {},
                'admin_levels': {}
            }
            for x in fields
        }  # Keep track of geo type and admin level counts

        fields_default_types = {x.id: x.type for x in fields}

        total_rows = len(data)

        for row in data:
            for k, v in row.items():

                if not k.isnumeric():  # because k is the pk of field
                    continue
                key = int(k)

                type = Field.STRING
                geo_parsed = None
                if parse_number(v):
                    type = Field.NUMBER
                elif parse_datetime(v):
                    type = Field.DATETIME
                else:
                    geo_parsed = parse_geo(v, geos_names, geos_codes)
                    if geo_parsed:
                        type = Field.GEO
                        geo_type = geo_parsed['geo_type']
                        admin_level = geo_parsed['admin_level']

                        geo_counts[key]['geo_types'][geo_type] = \
                            geo_counts[key]['geo_types'].get(geo_type, 0) + 1

                        geo_counts[key]['admin_levels'][admin_level] = \
                            geo_counts[key]['admin_levels'].\
                            get(admin_level, 0) + 1
                    else:
                        type = Field.STRING

                #  Update types count
                fields_types_count[key][type] = \
                    fields_types_count[key].get(type, 0) + 1

        # Threshold percent for types to be same for a field
        threshold_count = math.floor(AUTO_DETECT_THRESHOLD * total_rows)

        for field in fields:
            detected_field_type = [
                k for k, v in fields_types_count[field.id].items()
                if v >= threshold_count
            ]
            type = detected_field_type[0] if detected_field_type \
                else fields_default_types[field.id]

            #  Get admin_level and geo_type for geo type field
            if type == Field.GEO:
                geo_type = max(
                    geo_counts[field.id]['geo_types'].items(),
                    key=lambda kv: kv[1]
                )[0]
                admin_level = max(
                    geo_counts[field.id]['admin_levels'].items(),
                    key=lambda kv: kv[1]
                )[0]
                field.options = {
                    'geo_type': geo_type,
                    'admin_level': admin_level
                }

            field.type = type
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
        query = row.get(str(field.pk))
        geoareas = project_geoareas.annotate(
            similarity=search.TrigramSimilarity('title', query),
        ).filter(similarity__gt=0.2).order_by('-similarity')
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

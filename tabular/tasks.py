import traceback
import logging
import math

from celery import shared_task
from redis_store import redis
from django.db import transaction
from django.contrib.postgres import search

from geo.models import models, GeoArea

from .models import Book, Field, Geodata
from .extractor import csv, xlsx
from .utils import (
    parse_number,
    parse_datetime,
    parse_geo,
    get_geos_dict,
)
from utils.common import get_max_occurence_and_count


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

        total_rows = len(data)

        for row in data:
            for k, v in row.items():
                # field_id: {'value': XXX, type: type}

                if not k.isnumeric():  # because k is the pk of field
                    continue

                type = Field.STRING
                geo_parsed = None
                if parse_number(v['value']):
                    type = Field.NUMBER
                elif parse_datetime(v['value']):
                    type = Field.DATETIME
                else:
                    geo_parsed = parse_geo(v['value'], geos_names, geos_codes)

                if geo_parsed is not None:
                    type = Field.GEO
                    v['geo_type'] = geo_parsed['geo_type']
                    v['admin_level'] = geo_parsed['admin_level']

                v['type'] = type

        # Store types info in row data
        sheet.data = data
        sheet.save()

        # Threshold percent for types to be same for a field
        threshold_count = math.floor(AUTO_DETECT_THRESHOLD * total_rows)

        for field in fields:
            fid = str(field.id)
            id_types = [row[fid]['type'] for row in data]
            max_type, max_count = get_max_occurence_and_count(id_types)

            type = field.type
            if max_count >= threshold_count:
                type = max_type

            #  Get admin_level and geo_type for geo type field
            if type == Field.GEO:
                geo_types = [
                    row[fid]['geo_type']
                    for row in data
                    if row[fid]['type'] == Field.GEO
                ]
                admin_levels = [
                    row[fid]['admin_level']
                    for row in data
                    if row[fid]['type'] == Field.GEO
                ]

                max_type, type_count = get_max_occurence_and_count(geo_types)
                max_lev, lev_count = get_max_occurence_and_count(admin_levels)

                field.options = {
                    'geo_type': max_type,
                    'admin_level': max_lev
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

    is_code = field.get_option('geo_type', 'name') == 'code'
    admin_level = field.get_option('admin_level')
    if admin_level:
        project_geoareas = project_geoareas.filter(
            admin_level__level=admin_level
        )

    for row in geodata.field.sheet.data:
        similar_areas = []
        query = row.get(str(field.pk))

        if is_code:
            geoareas = project_geoareas.filter(code=query).annotate(
                similarity=models.Value(1, models.FloatField()),
            )
        else:
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

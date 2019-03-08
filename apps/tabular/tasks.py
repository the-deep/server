import traceback
import logging

from celery import shared_task
from redis_store import redis
from django.db import transaction
from django.contrib.postgres import search

from geo.models import models, GeoArea

from utils.common import redis_lock, LogTime

from .models import Book, Geodata, Field
from .extractor import csv, xlsx
from .viz.renderer import (
    calc_preprocessed_data,
    render_field_chart,
)
from .utils import (
    get_geos_dict,
    sample_and_detect_type_and_options,
)

logger = logging.getLogger(__name__)

AUTO_DETECT_THRESHOLD = 0.8
# Means, 80% of entries in a column should be of same type in order for column
# to be of that type


def _tabular_extract_book(book):
    if book.file_type == Book.CSV:
        csv.extract(book)
    elif book.file_type == Book.XLSX:
        xlsx.extract(book)
    auto_detect_and_update_fields(book)
    return True


@LogTime()
def auto_detect_and_update_fields(book):
    # TODO: Find some ways to lazily calculate geos_names, geos_codes
    geos_names = get_geos_dict(book.project)
    geos_codes = {v['code'].lower(): v for k, v in geos_names.items()}

    def isValueNotEmpty(v):
        return v.get('value')

    generate_column_columns = []

    with transaction.atomic():
        for sheet in book.sheet_set.all():
            fields = sheet.field_set.all()

            for field in fields:
                emptyFiltered = list(filter(isValueNotEmpty, field.data))
                detected_info = sample_and_detect_type_and_options(
                    emptyFiltered, geos_names, geos_codes
                )
                field.type = detected_info['type']
                field.options = detected_info['options']

                cast_info = field.cast_data(geos_names, geos_codes)
                field.data = cast_info['values']
                field.options = cast_info['options']
                with LogTime(
                        block_name='Field Save, size: {}, type: {}'.format(
                            len(cast_info['values']), field.type
                        )):
                    field.cache = {'status': Field.CACHE_PENDING}
                    field.save()

                generate_column_columns.append(field.id)

    # Start chart generation tasks
    tabular_generate_columns_image.s(generate_column_columns).delay()


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


def _tabular_render_field_chart(field):
    pass


def _tabular_calc_preprocessed_data(field_id):
    try:
        field = Field.objects.get(pk=field_id)
        return calc_preprocessed_data(field)
    except Field.DoesNotExist:
        logger.warn('Field ({}) doesn\'t exists'.format(field_id))


@shared_task
@redis_lock
def tabular_generate_column_image(field_id):
    try:
        field = Field.objects.get(pk=field_id)
        calc_preprocessed_data(field)
        return render_field_chart(field)
    except Field.DoesNotExist:
        logger.warn('Field ({}) doesn\'t exists'.format(field_id))


@shared_task
def tabular_generate_columns_image(fields_id):
    for field in Field.objects.filter(pk__in=fields_id):
        calc_preprocessed_data(field)
    for field in Field.objects.filter(pk__in=fields_id):
        render_field_chart(field)


@shared_task
@LogTime()
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

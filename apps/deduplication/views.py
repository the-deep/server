from typing import Optional
from django.http import Http404
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.request import Request

from core.models import ToFetchProject
from .tasks.callback import process_dedup_request
from .models import LSHIndex, DeduplicationRequest
from .serializers import DeduplicationRequestSerializer

DEDUP_SUCCESS_RESP = Response(
    {
        "message": "Deduplication request has been successfully queued",
    },
    status=status.HTTP_202_ACCEPTED,
)


@api_view(["POST"])
@transaction.atomic
def deduplication(request: Request):
    serializer = DeduplicationRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    prj_id = serializer.validated_data["project_id"]
    to_fetch_project: Optional[ToFetchProject] = ToFetchProject.objects.filter(
        original_project_id=prj_id,
    ).first()
    req_obj: DeduplicationRequest = serializer.save()

    if to_fetch_project is None:
        # Create one
        ToFetchProject.objects.create(
            original_project_id=prj_id,
            is_added_manually=False,  # Because this is not manual intention and triggered by DEEP
        )
        return DEDUP_SUCCESS_RESP

    if to_fetch_project.status != ToFetchProject.FetchStatus.FETCHED:
        # return for now, it will be fetched later and subsequent indexing will happen
        return DEDUP_SUCCESS_RESP

    lshindex: Optional[LSHIndex] = LSHIndex.objects.filter(
        project__original_project_id=prj_id
    ).first()
    if lshindex is None or lshindex.status != LSHIndex.IndexStatus.CREATED:
        # return for now, subsequent indexing will happen later
        return DEDUP_SUCCESS_RESP

    # All is good, the project has corresponding lsh index created. Proceeed to
    # further processing of the request
    process_dedup_request.delay(req_obj.pk)

    return DEDUP_SUCCESS_RESP

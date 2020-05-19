import django_filters
from django.db import models
from rest_framework.decorators import action
from rest_framework import (
    views,
    viewsets,
    response,
    permissions,
    exceptions,
)

from deep.permissions import ModifyPermission

from .utils import xls_form, kobo_toolbox

from .models import (
    QuestionBase,
    FrameworkQuestion,
    Questionnaire,
    Question,
    CrisisType,
)

from .serializers import (
    CrisisTypeSerializer,
    MiniQuestionnaireSerializer,
    QuestionnaireSerializer,
    QuestionSerializer,
    FrameworkQuestionSerializer,
    XFormSerializer,
    KoboToolboxExportSerializer,
)

from .filter_set import QuestionnaireFilterSet


class QuestionnaireViewSet(viewsets.ModelViewSet):
    serializer_class = QuestionnaireSerializer
    # TODO: Create Permission
    permission_classes = (permissions.IsAuthenticated, ModifyPermission)

    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = QuestionnaireFilterSet

    def get_queryset(self):
        return Questionnaire.objects.annotate(
            active_questions_count=models.Count(
                'question', filter=models.Q(question__is_archived=False), distinct=True
            )
        ).prefetch_related('crisis_types')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if 'pk' in self.kwargs:
            context['questionnaire_id'] = self.kwargs['pk']
        return context

    def get_serializer_class(self):
        if self.action == 'list':
            return MiniQuestionnaireSerializer
        return super().get_serializer_class()

    @action(
        detail=False,
        url_path='options',
    )
    def get_options(self, request, version=None):
        options = {
            field: [
                {'key': key, 'value': value}
                for key, value in values
            ]
            for field, values in (
                ('enumerator_skill_options', QuestionBase.ENUMERATOR_SKILL_OPTIONS),
                ('data_collection_technique_options', QuestionBase.DATA_COLLECTION_TECHNIQUE_OPTIONS),
                ('question_importance_options', QuestionBase.IMPORTANCE_OPTIONS),
                ('question_type_options', QuestionBase.TYPE_OPTIONS),
            )
        }
        options['crisis_type_options'] = CrisisTypeSerializer(
            CrisisType.objects.all(),
            many=True,
        ).data
        return response.Response(options)

    @action(detail=True, methods=['post'], url_path='clone')
    def create_clone(self, request, *args, **kwargs):
        """
        Clone questionnaire (also questions)

        Available override fields
        ```python
        ['title', 'crisisTypesId', 'projectId', 'requiredDuration', 'dataCollectionTechnique', 'enumeratorSkill']
        ```
        """
        obj = self.get_object()
        questions = obj.question_set.all()
        old_crisis_types = obj.crisis_types.all()
        new_questions = []
        obj.pk = None

        # Override fields value if supplied
        [
            setattr(obj, field, value)
            for field in [
                'title', 'project_id', 'required_duration',
                'data_collection_technique', 'enumerator_skill'
            ]
            for value in [request.data.get(field)]
            if value is not None
        ]
        obj.save()

        # Override crisis types
        override_crisis_types_id = request.data.get('crisis_types_id')
        if override_crisis_types_id is not None:
            old_crisis_types = CrisisType.objects.filter(pk__in=override_crisis_types_id)
        obj.crisis_types.set(old_crisis_types, clear=True)

        for question in questions:
            question.pk = None
            question.questionnaire = obj
            new_questions.append(question)
        Question.objects.bulk_create(new_questions)
        return response.Response(self.get_serializer_class()(obj).data)


class QuestionBaseViewMixin():
    @action(detail=False, methods=['post'], url_path='bulk-delete')
    def bulk_delete(self, *args, **kwargs):
        """{"id": number}"""
        return self.bulk_action()

    @action(detail=False, methods=['post'], url_path='bulk-archive')
    def bulk_archive(self, *args, **kwargs):
        """{"id": number}"""
        return self.bulk_action()

    @action(detail=False, methods=['post'], url_path='bulk-unarchive')
    def bulk_unarchive(self, *args, **kwargs):
        """{"id": number}"""
        return self.bulk_action()

    def bulk_action(self):
        # TODO: Permission
        try:
            question_body = {q['id']: q for q in self.request.data}
        except (TypeError, KeyError):
            raise exceptions.ValidationError('Invalid request. Check and try again!!')
        questions = self.get_queryset().filter(id__in=question_body.keys())
        response_body = list(questions.values_list('id', flat=True))

        if self.action == 'bulk_delete':
            questions.all().delete()
        elif self.action == 'bulk_archive':
            questions.update(is_archived=True)
        elif self.action == 'bulk_unarchive':
            questions.update(is_archived=False)
        elif self.action == 'bulk_order':
            # TODO: Use bulk update after django upgrade
            updated_questions = []
            for question in questions.all():
                question.order = question_body.get(question.id).get('order')
                if question.order is None:
                    continue
                question.save()
                updated_questions.append({'id': question.pk, 'new_order': question.order})
            response_body = updated_questions
        return response.Response(response_body)

    @action(detail=True, methods=['post'], url_path='order')
    def order(self, request, *args, **kwargs):
        """
        ```json
        {
          "action": "below|above|top|bottom",
          "value": "Question id required for below|above"
        }
        ```
        """
        # TODO: Permission
        question = self.get_object()
        QuestionSerializer.apply_order_action(question, request.data)
        if isinstance(question, FrameworkQuestion):
            return response.Response({
                'new_order': question.analysis_framework.question_set.order_by('order').values_list('pk', flat=True)
            })
        return response.Response({
            'new_order': question.questionnaire.question_set.order_by('order').values_list('pk', flat=True),
        })

    @action(detail=True, methods=['post'], url_path='clone')
    def create_clone(self, request, *args, **kwargs):
        """
        Clone Question (Deprecated)
        ```json
        {"order_action": {'action' and 'value'}}
        ```
        """
        obj = self.get_object()
        obj.pk = None
        obj.order = None
        obj.save()
        QuestionSerializer.apply_order_action(obj, request.data.get('order_action', {}), 'bottom')
        return response.Response(self.get_serializer_class()(obj).data)


class QuestionViewSet(QuestionBaseViewMixin, viewsets.ModelViewSet):
    serializer_class = QuestionSerializer
    # TODO: Create Permission
    permission_classes = (permissions.IsAuthenticated, ModifyPermission)

    def get_queryset(self):
        return Question.objects.filter(questionnaire=self.kwargs['questionnaire_id']).all()

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'questionnaire_id': self.kwargs.get('questionnaire_id'),
        }

    @action(detail=False, methods=['post'], url_path=r'af-question-copy')
    def copy_from_af_question(self, request, *args, **kwargs):
        """
        Copy from framework question to Questionnaire question
        ```json
        {"framework_question_id": <numberid>, "order_action": {'action': and 'value'}}
        ```
        """
        try:
            fq = FrameworkQuestion.objects.get(id=request.data['framework_question_id'])
            questionnaire = Questionnaire.objects.get(id=self.kwargs['questionnaire_id'])
        except (TypeError, KeyError):
            raise exceptions.ValidationError('Invalid request. Check and try again!!')

        if not (fq.can_get(request.user) and questionnaire.can_modify(request.user)):
            return exceptions.PermissionDenied()

        # Permissions
        new_question = Question.objects.create(
            cloned_from=fq,
            questionnaire=questionnaire,
            order=None,
            **{
                field.name: getattr(fq, field.name)
                for field in fq._meta.fields if field.name not in ['id', 'order']
            },
        )
        QuestionSerializer.apply_order_action(new_question, request.data.get('order_action', {}), 'bottom')
        return response.Response(self.get_serializer_class()(new_question).data)


class FrameworkQuestionViewSet(QuestionBaseViewMixin, viewsets.ModelViewSet):
    serializer_class = FrameworkQuestionSerializer
    # TODO: Create Permission
    permission_classes = (permissions.IsAuthenticated, ModifyPermission)

    def get_serializer_context(self):
        return {
            **super().get_serializer_context(),
            'af_id': self.kwargs.get('af_id'),
        }

    def get_queryset(self):
        return FrameworkQuestion.objects.filter(analysis_framework=self.kwargs['af_id']).all()


class XFormView(views.APIView):
    def get_serializer(self, *args, **kwargs):
        return XFormSerializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        xlsform_file = serializer.validated_data['file']
        try:
            return response.Response(xls_form.XLSForm.create_enketo_form(xlsform_file))
        except Exception:
            raise exceptions.ValidationError('Invalid request. Please provide valid XLSForm file!!')


class KoboToolboxExport(views.APIView):
    def get_serializer(self, *args, **kwargs):
        return KoboToolboxExportSerializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        xlsform_file = serializer.validated_data['file']
        req_vd = serializer.validated_data

        kt = kobo_toolbox.KoboToolbox(username=req_vd['username'], password=req_vd['password'])
        try:
            return response.Response(kt.export(xlsform_file))
        except Exception:
            raise exceptions.ValidationError(
                'Invalid request. Please provide valid XLSForm file and valid access token!!')

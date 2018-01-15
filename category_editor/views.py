from rest_framework import (
    exceptions,
    permissions,
    response,
    status,
    views,
    viewsets,
)
from deep.permissions import ModifyPermission

from project.models import Project
from lead.models import LeadPreview
from .models import CategoryEditor
from .serializers import CategoryEditorSerializer

import re


class CategoryEditorViewSet(viewsets.ModelViewSet):
    serializer_class = CategoryEditorSerializer
    permission_classes = [permissions.IsAuthenticated,
                          ModifyPermission]

    def get_queryset(self):
        return CategoryEditor.get_for(self.request.user)


class CategoryEditorCloneView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, ce_id, version=None):
        if not CategoryEditor.objects.filter(
            id=ce_id
        ).exists():
            raise exceptions.NotFound()

        category_editor = CategoryEditor.objects.get(
            id=ce_id
        )
        if not category_editor.can_get(request.user):
            raise exceptions.PermissionDenied()

        new_ce = category_editor.clone(request.user)
        serializer = CategoryEditorSerializer(
            new_ce,
            context={'request': request},
        )

        project = request.data.get('project')
        if project:
            project = Project.objects.get(id=project)
            if not project.can_modify(request.user):
                raise exceptions.ValidationError({
                    'project': 'Invalid project',
                })
            project.category_editor = new_ce
            project.modified_by = request.user
            project.save()

        return response.Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
        )


class CategoryEditorClassifyView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, project_id, version=None):
        if not Project.objects.filter(id=project_id).exists():
            raise exceptions.NotFound()

        project = Project.objects.get(id=project_id)
        if not project.can_get(request.user):
            raise exceptions.PermissionDenied()

        if not project.category_editor:
            raise exceptions.NotFound()

        ce_data = project.category_editor.data
        category = request.data.get('category')
        text = request.data.get('text')
        preview_id = request.data.get('preview_id')

        errors = {}
        if not category:
            errors['category'] = 'Value not provided'
        if not text and not preview_id:
            errors['text'] = 'Value not provided'
            errors['preview_id'] = 'Value not provided'

        if not text:
            text = LeadPreview.objects.get(id=preview_id).text_extract
            # TODO: Raise error if preview_id is invalid

        if errors:
            raise exceptions.ValidationError(errors)

        classifications = self._classify(ce_data, category, text)

        return response.Response(
            {
                'classifications': classifications,
            },
            status=status.HTTP_200_OK,
        )

    def _classify(self, ce_data, category, text):
        category = next((
            c for c in
            ce_data.get('categories')
            if c.get('title').lower() == category.lower()
        ), None)

        if not category:
            return []

        results = []
        subcategories = category.get('subcategories', [])

        for subcategory in subcategories:
            self._process_subcategory(subcategory, text.lower(), results)

        return results

    def _process_subcategory(self, category, text, results):
        title = category.get('title')
        ngrams = category.get('ngrams', {})

        category_results = []
        results.append({
            'title': title,
            'keywords': category_results,
        })

        for _, ngram in ngrams.items():
            [
                category_results.extend(self._search_word(title, word, text))
                for word in ngram
                if word.lower() in text
            ]

        subcategories = category.get('subcategories', [])
        for subcategory in subcategories:
            self._process_subcategory(subcategory, text, results)

    def _search_word(self, title, word, text):
        return [
            {
                'start': a.start(),
                'length': len(word),
                'subcategory': title,
            } for a in list(re.finditer(word, text))
        ]

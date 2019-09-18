from django import forms

from .permissions import PROJECT_PERMISSIONS
from .widgets import PermissionsWidget
from .models import ProjectRole


class ProjectRoleForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['lead_permissions'].widget = PermissionsWidget(
            'lead_permissions',  # NOTE: this needs to besent to uniquely identify the checkboxes
            PROJECT_PERMISSIONS.lead,
        )
        self.fields['entry_permissions'].widget = PermissionsWidget(
            'entry_permissions',
            PROJECT_PERMISSIONS.entry,
        )
        self.fields['setup_permissions'].widget = PermissionsWidget(
            'setup_permissions',
            PROJECT_PERMISSIONS.setup,
        )
        self.fields['export_permissions'].widget = PermissionsWidget(
            'export_permissions',
            PROJECT_PERMISSIONS.export,
        )
        self.fields['assessment_permissions'].widget = PermissionsWidget(
            'assessment_permissions',
            PROJECT_PERMISSIONS.assessment,
        )

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.lead_permissions = self.cleaned_data['lead_permissions']
        obj.entry_permissions = self.cleaned_data['entry_permissions']
        obj.setup_permissions = self.cleaned_data['setup_permissions']
        obj.export_permissions = self.cleaned_data['export_permissions']
        obj.assessment_permissions = self.cleaned_data['assessment_permissions']

        obj.save()
        self.save_m2m()
        return obj

    class Meta:
        model = ProjectRole
        fields = '__all__'

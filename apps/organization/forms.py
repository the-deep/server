from django import forms
from .models import Organization


class MergeForm(forms.Form):
    parent_organization = forms.ModelChoiceField(
        queryset=Organization.objects.none(),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        qs = kwargs.pop('organizations')
        super().__init__(*args, **kwargs)
        self.fields['parent_organization'].queryset = qs

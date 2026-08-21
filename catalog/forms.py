"""Server-validated inputs for catalog administration."""

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from catalog.models import TrackVersion


class TrackForm(forms.Form):
    title = forms.CharField(label="Título", max_length=160, strip=True)
    description = forms.CharField(
        label="Descripción",
        max_length=2000,
        strip=True,
        widget=forms.Textarea,
    )
    audience = forms.CharField(label="Audiencia", max_length=500, strip=True)
    expected_revision = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput,
    )


class PublicationMetadataForm(forms.Form):
    source = forms.CharField(label="Fuente", max_length=500, strip=True)
    reviewed_on = forms.DateField(label="Fecha de revisión")
    editorial_status = forms.ChoiceField(
        label="Estado editorial",
        choices=TrackVersion.EditorialStatus.choices,
    )

    def clean_reviewed_on(self):
        reviewed_on = self.cleaned_data["reviewed_on"]
        if reviewed_on > timezone.localdate():
            raise ValidationError("La fecha de revisión no puede ser futura.")
        return reviewed_on


class TrackPositionForm(forms.Form):
    position = forms.IntegerField(label="Posición")
    expected_order_revision = forms.IntegerField(
        min_value=0,
        widget=forms.HiddenInput,
    )


class TrackStateForm(PublicationMetadataForm):
    expected_revision = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class TrackDeactivateForm(forms.Form):
    expected_revision = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class ModuleForm(forms.Form):
    title = forms.CharField(label="Título", max_length=160, strip=True)
    objective = forms.CharField(
        label="Objetivo",
        max_length=1000,
        strip=True,
        widget=forms.Textarea,
    )
    expected_revision = forms.IntegerField(
        min_value=1,
        required=False,
        widget=forms.HiddenInput,
    )


class ModulePositionForm(TrackPositionForm):
    pass

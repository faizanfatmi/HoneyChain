from django import forms

from .models import Batch, Beekeeper, Block, Hive

_TEXT = {"class": "field-input"}
_SELECT = {"class": "field-input"}


class BeekeeperForm(forms.ModelForm):
    class Meta:
        model = Beekeeper
        fields = ["name", "apiary_reg_no", "location", "state", "phone", "certified_organic"]
        widgets = {
            "name": forms.TextInput(attrs=_TEXT),
            "apiary_reg_no": forms.TextInput(attrs=_TEXT),
            "location": forms.TextInput(attrs=_TEXT),
            "state": forms.TextInput(attrs=_TEXT),
            "phone": forms.TextInput(attrs=_TEXT),
        }


class HiveForm(forms.ModelForm):
    class Meta:
        model = Hive
        fields = ["beekeeper", "code", "floral_source", "latitude", "longitude"]
        widgets = {
            "beekeeper": forms.Select(attrs=_SELECT),
            "code": forms.TextInput(attrs={**_TEXT, "placeholder": "HIVE-XX-000"}),
            "floral_source": forms.TextInput(attrs={**_TEXT, "placeholder": "Mustard / Litchi / Multiflora"}),
            "latitude": forms.NumberInput(attrs=_TEXT),
            "longitude": forms.NumberInput(attrs=_TEXT),
        }


class BatchForm(forms.ModelForm):
    class Meta:
        model = Batch
        fields = ["hive", "honey_type", "harvest_date", "quantity_kg"]
        widgets = {
            "hive": forms.Select(attrs=_SELECT),
            "honey_type": forms.TextInput(attrs={**_TEXT, "placeholder": "Raw Mustard Honey"}),
            "harvest_date": forms.DateInput(attrs={**_TEXT, "type": "date"}),
            "quantity_kg": forms.NumberInput(attrs=_TEXT),
        }


class EventForm(forms.Form):
    event_type = forms.ChoiceField(
        choices=[c for c in Block.Event.choices if c[0] != Block.Event.GENESIS],
        widget=forms.Select(attrs=_SELECT),
    )
    actor = forms.CharField(
        max_length=160,
        widget=forms.TextInput(attrs={**_TEXT, "placeholder": "e.g. Nashik Processing Unit"}),
    )
    location = forms.CharField(
        max_length=160, required=False, widget=forms.TextInput(attrs=_TEXT)
    )
    note = forms.CharField(
        required=False, widget=forms.Textarea(attrs={**_TEXT, "rows": 2})
    )
    moisture_pct = forms.FloatField(
        required=False, label="Moisture %", widget=forms.NumberInput(attrs=_TEXT)
    )
    pollen_count = forms.IntegerField(
        required=False, label="Pollen count", widget=forms.NumberInput(attrs=_TEXT)
    )
    temperature_c = forms.FloatField(
        required=False, label="Temperature °C", widget=forms.NumberInput(attrs=_TEXT)
    )

    def metrics(self):
        keys = ["moisture_pct", "pollen_count", "temperature_c"]
        return {k: self.cleaned_data[k] for k in keys if self.cleaned_data.get(k) is not None}

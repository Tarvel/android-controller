from django import forms
from web.controller.models import Session


class SessionForm(forms.ModelForm):
    class Meta:
        model = Session
        fields = ["device", "title", "mode"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Session title"}),
        }

from django import forms
from django.conf import settings
from uploader.models import Resource


class ResourceStageOneForm(forms.Form):
    class Meta:
        model = Resource
    
    file = forms.FileField(required=False)
    link = forms.CharField(required=False)
        
        
class ResourceStageTwoForm(forms.ModelForm):
    class Meta:
        model = Resource
        exclude = ('approved',)
        widgets = {
            'link': forms.HiddenInput(),
            'file': forms.HiddenInput(),
            'uploader': forms.HiddenInput()
        }
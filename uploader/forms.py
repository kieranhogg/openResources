from django import forms
from django.conf import settings
from uploader.models import Resource


class ResourceStageOneForm(forms.Form):
    file = forms.FileField(required=False)
    link = forms.CharField(required=False)
    
    class Meta:
        model = Resource
    
        
class ResourceStageTwoForm(forms.ModelForm):

    class Meta:
        model = Resource
        exclude = ('approved',)
        widgets = {
            'link': forms.HiddenInput(),
            'file': forms.HiddenInput(),
            'uploader': forms.HiddenInput(),
        }
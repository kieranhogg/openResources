from django import forms
from django.conf import settings
from uploader.models import Resource, Bookmark, File


class BookmarkStageOneForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        exclude = ('approved',)
        widgets = {
            'description': forms.Textarea(),
            'uploader': forms.HiddenInput(),
        }
    
 
class FileStageOneForm(forms.ModelForm):
    class Meta:
        model = File
        exclude = ('approved', 'uploader', 'mimetype', 'filesize', 'filename', 
            'date_pub')
        widgets = {'description': forms.Textarea()}
       
        
class ResourceStageTwoForm(forms.ModelForm):
    class Meta:
        model = Resource
        exclude = ('approved',)
        widgets = {
            'bookmark': forms.HiddenInput(),
            'file': forms.HiddenInput(),
            'uploader': forms.HiddenInput(),
        }
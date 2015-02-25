from django import forms
from django.conf import settings
from uploader.models import (Resource, Bookmark, File, Subject, Syllabus, Unit,
    UnitTopic)



class BookmarkStageOneForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        exclude = ('approved',)
        widgets = {
            'description': forms.Textarea(),
            'uploader': forms.HiddenInput(),
        }
    
 
class FileStageOneForm(forms.ModelForm):
    i_am_the_author = forms.BooleanField()
    
    class Meta:
        model = File
        exclude = ('approved', 'uploader', 'mimetype', 'filesize', 'filename', 
            'date_pub', 'topics')
        widgets = {'description': forms.Textarea()}
        fields = ('title', 'file', 'description', 'type', 'i_am_the_author', 
            'author', 'author_link', 'licence')

        
class ResourceStageTwoForm(forms.ModelForm):
    class Meta:
        model = Resource
        exclude = ('approved',)
        widgets = {
            'bookmark': forms.HiddenInput(),
            'file': forms.HiddenInput(),
            'uploader': forms.HiddenInput(),
        }
        
    def clean(self):
        cleaned_data = super(ResourceStageTwoForm, self).clean()
        unit = cleaned_data.get("unit")
        unit_topic = cleaned_data.get("unit_topic")

        if unit_topic and not unit:
            raise forms.ValidationError("You can't set a unit topic without " + 
                " a unit")

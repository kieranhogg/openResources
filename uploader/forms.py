from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from uploader.models import (Resource, Bookmark, File, Subject, Syllabus, Unit,
                             UnitTopic, Note)
                        

class BookmarkStageOneForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        exclude = ('approved','slug')
        widgets = {
            'description': forms.Textarea(),
            'uploader': forms.HiddenInput(),
        }


class FileStageOneForm(forms.ModelForm):
    i_am_the_author = forms.BooleanField(required=False)

    class Meta:
        model = File
        exclude = ('approved', 'uploader', 'mimetype', 'filesize', 'filename',
                   'date_pub', 'topics', 'slug')
        widgets = {'description': forms.Textarea()}
        fields = ('title', 'file', 'description', 'type', 'i_am_the_author',
                  'author', 'author_link', 'licence')

    def clean(self):
        valid = super(FileStageOneForm, self).is_valid()
        #data = self.cleaned_data
        data = super(FileStageOneForm, self).clean()
        try:
            if data.content_type in settings.UPLOAD_FILE_TYPES:
                if data.size > settings.UPLOAD_FILE_MAX_SIZE:
                    raise forms.ValidationError(_(
                        'File size must be under%s, yours was %s.') %
                        (filesizeformat(settings.UPLOAD_FILE_MAX_SIZE),
                         filesizeformat(data.size)))
                else:
                    raise forms.ValidationError(_(
                        'File type (%s) not supported.') % data.content_type)
        except AttributeError:
            pass


class ResourceStageTwoForm(forms.ModelForm):
    class Meta:
        model = Resource
        exclude = ('approved', 'slug')
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

class NotesForm(forms.ModelForm):
    class Meta:
        model = Note
        exclude = ('slug','unit_topic')
    
    # def __init__(self, *args, **kwargs):
    #     super(NotesForm, self).__init__(*args, **kwargs)
    #     instance = getattr(self, 'instance', None)
    #     if instance and instance.pk:
    #         self.fields['unit_topic'].widget.attrs['readonly'] = True

    # def clean_unit_topic(self):
    #     instance = getattr(self, 'instance', None)
    #     if instance and instance.pk:
    #         return instance.unit_topic
    #     else:
    #         return self.cleaned_data['unit_topic']
            
    # def save(self, *args, **kwargs):
 	  #  if not 'pk' in self:
 	  #      unit_topic = get_object_or_404(UnitTopic, pk=self.cleaned_data.get('unit_topic').id)
 	  #      unit = unit_topic.unit
 	  #      self.slug = slugify(unit.title + ' ' + unit_topic.title)
 	  #      self.cleaned_data['slug'] = self.slug
    #  	    super(NotesForm, self).save(*args, **kwargs)

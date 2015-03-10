from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from uploader.models import (Resource, Bookmark, File, Subject, Syllabus, Unit,
    UnitTopic, Note, Image, MultipleChoiceQuestion, UserProfile)
                        

class BookmarkForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        exclude = ('approved','slug', 'uploader')
        widgets = {
            'description': forms.Textarea(),
        }


class FileForm(forms.ModelForm):
    class Meta:
        model = File
        exclude = ('approved', 'uploader', 'mimetype', 'filesize', 'filename',
                   'date_pub', 'topics', 'slug')
        widgets = {'description': forms.Textarea()}


    def clean(self):
        valid = super(FileForm, self).is_valid()
        #data = self.cleaned_data
        data = super(FileForm, self).clean()
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
    
class LinkResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        exclude = ('approved', 'slug', 'bookmark', 'file', 'uploader')

    def clean(self):
        cleaned_data = super(LinkResourceForm, self).clean()
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

class ImageForm(forms.ModelForm):
    class Meta:
        model = Image
        widgets = {
            'uploader': forms.HiddenInput(),
        }
        
class MultipleChoiceQuestionForm(forms.ModelForm):
    answer1 = forms.CharField(label='First answer')
    answer2 = forms.CharField(label='Second answer')
    answer3 = forms.CharField(label='Third answer', required=False)
    answer4 = forms.CharField(label='Fourth answer', required=False)
    add_another = forms.BooleanField(label='Add another question?', 
                                     required=False)
    
    class Meta:
        model = MultipleChoiceQuestion
        exclude = ('unit_topic', 'uploader')
        
# class SignupForm(forms.ModelForm):
#     # user = forms.CharField(max_length=40, label='Username')
#     # password = forms.CharField(max_length=40, label='Password')
#     # type = forms.CharField()
    
#     def __init__(self, *args, **kwargs):
#         super(SignupForm, self).__init__(*args, **kwargs)
        
#     def signup(self, request, user):
#         wsData = UserProfile()
#         wsData.user = user
#         wsData.wsUser = self.cleaned_data['user']
#         wsData.wsPwd = self.cleaned_data['password']
#         wsData.save()
#     class Meta:
#         model = UserProfile
#         # fields = ('user', 'password',)
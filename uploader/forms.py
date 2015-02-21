from django import forms
from django.conf import settings

from uploader.models import Subject, ExamLevel, Syllabus, Resource, Unit, UnitTopic, Licence, Topic

class ResourceForm(forms.ModelForm):
    file = forms.FileField()
    class Meta:
        model = Resource
        exclude = ('syllabus','unit','unittopic','topics', 'approved', 'file')

    # title = forms.CharField()
    # description = forms.CharField(widget=forms.Textarea)
    # file = forms.FileField()
    # #uploader = forms.ForeignKey(settings.AUTH_USER_MODEL)
    # author = forms.CharField(help_text='Who is the original author? E.g. John Smith. If you are ' + 
    #     'the author, write "me"')
    # author_link = forms.CharField(max_length=200, 
    #     help_text='A URL or email to credit the original author. If it is ' +
    #     'you, leave blank')
    #Don't really need but its for the forms, FIXME?
    subject = forms.ModelChoiceField(queryset=Subject.objects.all())
    # syllabus = forms.ModelChoiceField(queryset=Syllabus.objects.all())
    # unit = forms.ModelChoiceField(queryset=Unit.objects.all())
    # unittopic = forms.ModelChoiceField(queryset=UnitTopic.objects.all())
    # topics = forms.ModelMultipleChoiceField(
    #     queryset=Topic.objects.all(), 
    #     required=False,
    # )
    licence = forms.ModelChoiceField(queryset=Licence.objects.all())
    # def save(self):
    #     #content_type = self.cleaned_data['file'].content_type
    #     filename = "test.mp3"
    #     mimetype = "mp3"
    #     self.cleaned_data['file'] = SimpleUploadedFile(filename, self.cleaned_data['file'].read(), content_type)
    #     return super(ResourceForm, self).save()
        
    #def clean_file(self):
        # file = self.cleaned_data['file']
        # try:
        #     if file:
        #         file_type = file.content_type.split('/')[0]
        #         print file_type

        #         if len(file.name.split('.')) == 1:
        #             raise forms.ValidationError('File type is not supported')

        #         if file_type in settings.TASK_UPLOAD_FILE_TYPES:
        #             if file._size > settings.TASK_UPLOAD_FILE_MAX_SIZE:
        #                 raise forms.ValidationError('Please keep filesize under ' 
        #                 + settings.TASK_UPLOAD_FILE_MAX_SIZE + 'Current filesize: ' +
        #                 file._size)
        #         else:
        #             raise forms.ValidationError('File type is not supported')
        # except:
        #     pass
        #return file
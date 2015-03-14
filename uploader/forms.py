from django import forms
from django.conf import settings
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _
from django.utils.text import slugify
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from uploader.models import *


class BookmarkForm(forms.ModelForm):
    class Meta:
        model = Bookmark
        exclude = ('approved','slug', 'uploader', 'screenshot')
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
        
class StudentForm(forms.Form):
    group_code = forms.CharField(max_length=6,
        help_text="Your teacher will give you a class code to sign up")
    username = forms.CharField(max_length=30)
    first_name = forms.CharField()
    last_name = forms.CharField()
    password = forms.CharField(max_length=30,widget=forms.PasswordInput())
    password_again = forms.CharField(max_length=30,widget=forms.PasswordInput())
    email = forms.EmailField(required=False)
    
    def clean_username(self): # check if username dos not exist before
        try:
            User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist:
            return self.cleaned_data['username']
    
        raise forms.ValidationError("Username already taken")
    
    
    def clean(self): # check if password 1 and password2 match each other
        if 'password1' in self.cleaned_data and 'password2' in self.cleaned_data:
            if self.cleaned_data['password'] != self.cleaned_data['password_again']:
                raise forms.ValidationError("passwords do not match")
    
        return self.cleaned_data
    
    
    def save(self): # create new user
        new_user=User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'])
    
        up = StudentProfile(user=new_user,
                            forename=self.cleaned_data['first_name'],
                            surname=self.cleaned_data['last_name'])
        up.save()
        return new_user
        
class TeacherForm(forms.Form):
    title = forms.ChoiceField(choices=(('Mr', 'Mr'),
        ('Mrs', 'Mrs'), 
        ('Miss', 'Miss'),
        ('Ms', 'Ms'), 
        ('Dr', 'Dr')))
    username = forms.CharField(max_length=30)
    first_name = forms.CharField()
    last_name = forms.CharField()
    password=forms.CharField(label=_('Password'), max_length=30, 
        widget=forms.PasswordInput())
    password_again = forms.CharField(label=_('Password (again)'), max_length=30,
        widget = forms.PasswordInput())
    email=forms.EmailField(required=False, 
        help_text="Please use your school email to be verified, you can add " + 
            "a personal one later")
    
    def clean_username(self):
        try:
            User.objects.get(username=self.cleaned_data['username'])
        except User.DoesNotExist :
            return self.cleaned_data['username']
    
        raise forms.ValidationError("Username taken")
    
    
    def clean(self):
        if ('password' in self.cleaned_data and 'password_again' 
                in self.cleaned_data):
            if self.cleaned_data['password'] != self.cleaned_data['password_again']:
                raise forms.ValidationError("passwords dont match each other")
    
        return self.cleaned_data
    
    
    def save(self): # create new user
        new_user=User.objects.create_user(
            username=self.cleaned_data['username'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'])
                                            
        up = TeacherProfile(user=new_user, 
                            title=self.cleaned_data['title'],
                            forename=self.cleaned_data['first_name'],
                            surname=self.cleaned_data['last_name'])
        up.save()
        
        if settings.NEW_ACCOUNT_EMAIL:
            message = "A new teacher has signed up. \n\n"
            message += "Name: " + self.cleaned_data['first_name'] + " "
            message += self.cleaned_data['last_name'] + "\n"
            message += "Email: " + self.cleaned_data['email']
            
            send_mail('New Teacher', message, 'no_reply@eduresourc.es',
                settings.NEW_ACCOUNT_EMAIL, fail_silently=False)
        
        return new_user
        
class TeacherProfileForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        exclude = ('user', 'score', 'profile_setup')
        # widgets = {
        #             'title': forms.ChoiceField()
        #             }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        exclude = ('slug', 'uploader', 'url')
 
        
class LessonItemForm(forms.ModelForm):
    class Meta:
        model = LessonItem
        exclude = ('lesson', 'slug', 'type')
        
        
class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        exclude = ('teacher', 'code', 'slug')
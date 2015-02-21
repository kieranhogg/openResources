from django.db import models
from django.conf import settings
from django import forms
from django.forms import ModelForm
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.contrib.auth.models import AbstractUser

class Subject(models.Model):
    list_display = ('pub_date')
    def __unicode__(self):
       return self.subject_name
    subject_name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    pub_date = models.DateTimeField('date published')
    class Meta:
        ordering = ('subject_name',)

class ExamBoard(models.Model):
    list_display = ('board_name', 'pub_date')
    def __unicode__(self):
       return self.board_name
    board_name = models.CharField('Exam Board Name', max_length=200)
    pub_date = models.DateTimeField('date published')
    class Meta:
        ordering = ('board_name',)


class ExamLevel(models.Model):
    list_display = ('level_name', 'level_number', 'pub_date')
    def __unicode__(self):
       return self.level_name
    NONE = '0'
    KS3 = '3'
    KS4 = '4'
    KS5 = '5'
    YEAR_IN_SCHOOL_CHOICES = (
        (NONE, 'None'),
        (KS3, 'KS3'),
        (KS4, 'KS4'),
        (KS5, 'KS5'),
    )
    level_name = models.CharField('Exam Level', max_length=200)
    country = models.CharField('Country', max_length=200, default='Any')
    level_number = models.CharField(max_length=1,
                                      choices=YEAR_IN_SCHOOL_CHOICES,
                                      default=NONE)
    pub_date = models.DateTimeField('date published')
    class Meta:
        ordering = ('level_number','level_name')

    
class Syllabus(models.Model):
    list_display = ('subject', 'exam_board', 'exam_level', 'pub_date')
    def __unicode__(self):
        if str(self.exam_level) == str(self.exam_board):
            return str(self.exam_board) + ' ' + str(self.subject)
        else:
            return str(self.exam_board) + ' ' + str(self.subject) +  ' ' + str(self.exam_level) 
    subject = models.ForeignKey(Subject)
    exam_board = models.ForeignKey(ExamBoard)
    exam_level = models.ForeignKey(ExamLevel)
    pub_date = models.DateTimeField('date published')
    class Meta:
        ordering = ('exam_board','exam_level')
    
class Unit(models.Model):
    title = models.CharField('Title', max_length=200)
    syllabus = models.ForeignKey(Syllabus)
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text='A brief overview of the content'
    )
    pub_date = models.DateTimeField('date published')
    def __unicode__(self):
       return str(self.title) 
    class Meta:
        ordering = ('title',)
        
class Topic(models.Model):
    title = models.CharField('Title', max_length=200)
    #resource = models.ManyToManyField('uploader.Resource')
    def __unicode__(self):
       return str(self.title) 
    class Meta:
        ordering = ('title',)
    
class UnitTopic(models.Model):
    title = models.CharField('Title', max_length=200)
    unit = models.ForeignKey(Unit)
    topic = models.ManyToManyField(Topic, blank=True, null=True)
    description = models.TextField(
        blank=True, 
        null=True, 
        help_text='E.g. the expected topics taught'
    )
    pub_date = models.DateTimeField('date published')
    def __unicode__(self):
       return str(self.title)
    class Meta:
        ordering = ('title',)
    
class Document(models.Model):
    docfile = models.FileField()
    def __unicode__(self):
       return str(self.docfile)
    class Meta:
        ordering = ('docfile',)
        
class Licence(models.Model):
    name = models.CharField('Title', max_length=200)
    description = models.TextField('Description', null=True)
    link = models.CharField('URL', max_length=200)
    def __unicode__(self):
       return str(self.name)
      
class File(models.Model):
    filename = models.CharField('Filename', max_length=200)
    file = models.FileField()
    mimetype = models.CharField('Mimetype', max_length=200)
    pub_date = models.DateTimeField('date published', auto_now_add=True, blank=True)
    def __str__(self):
        return self.filename

class Resource(models.Model):
    PRESENTATION = 1
    LESSON_PLAN = 2
    SOW = 3
    WEBPAGE = 4
    VIDEO = 5

    RESOURCE_TYPES = (
        (PRESENTATION, 'A lesson presentation'),
        (LESSON_PLAN, 'A lesson plan'),
        (SOW, 'A scheme of work'),
        (WEBPAGE, 'A link to a webpage'),
        (VIDEO, 'A link to a video'),
    )
    list_display = ('title', 'approved')
    def __str__(self):
       return str(self.title)
    search_fields = ['title', 'approved']
    title = models.CharField('Title', max_length=200)
    description = models.TextField('Description', null=True)
    file = models.ForeignKey(File, blank=True, null=True)
    link = models.CharField(max_length=400, blank=True, null=True)
    type = models.IntegerField(max_length=2, default=1, choices=RESOURCE_TYPES)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    author = models.CharField('Author', max_length=200, null=True,
        help_text='Who is the original author? E.g. John Smith. If you are ' + 
        'the author, write "me"')
    author_link = models.CharField('Author Link', max_length=200, null=True, 
        help_text='A URL or email to credit the original author. If it is ' +
        'you, leave blank')
    #Don't really need but its for the forms, FIXME?
    subject = models.ForeignKey(Subject)
    syllabus = models.ForeignKey(Syllabus)
    unit = models.ForeignKey(Unit,  null=True, blank=True)
    unittopic = models.ForeignKey(UnitTopic, null=True, blank=True, 
        verbose_name="Unit Topic")
    topics = models.ManyToManyField(Topic)
    licence = models.ForeignKey(Licence, null=True, 
        help_text = mark_safe('<a href="uploader/licences/">Help with the licences</a>'))

    approved = models.BooleanField(default=False)
    pub_date = models.DateTimeField('date published', auto_now_add=True, blank=True)
    class Meta:
        ordering = ('title',)
        
class Rating(models.Model):
    AWFUL = 0
    VPOOR = 1
    POOR = 2
    MEDIOCRE = 3
    GOOD = 4
    VGOOD = 5
    
    RATING_CHOICES = (
        (AWFUL, 'Just awful'),
        (VPOOR, 'Very poor'),
        (POOR, 'Poor'),
        (MEDIOCRE, 'Mediocre'),
        (GOOD, 'Good'),
        (VGOOD, 'Very good'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    resource = models.ForeignKey(Resource)
    rating = models.IntegerField(max_length=1, choices=RATING_CHOICES)
    pub_date = models.DateTimeField(auto_now_add=True, blank=True)
   
class UserProfile(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    score = models.IntegerField(default=0)

# cleans up files from AWS when resource is deleted from DB
@receiver(pre_delete, sender=File)
def mymodel_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)
        
# class ResourceForm(ModelForm):
#     class Meta:
#         model = Resource
#         fields = ['title', 'description', 'file', 'author', 'author_link', 
#             'licence', 'subject', 'syllabus', 'unit', 'unittopic', 'topics', 'uploader']

    
    


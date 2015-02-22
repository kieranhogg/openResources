from django.db import models
from django.conf import settings
from django import forms
from django.forms import ModelForm
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.contrib.auth.models import AbstractUser


class Subject(models.Model):
    def __unicode__(self):
       return self.subject_name
       
    class Meta:
        ordering = ('subject_name',)
       
    subject_name = models.CharField(max_length = 200)
    active = models.BooleanField(default = True)
    pub_date = models.DateTimeField('Date published')
    
    
class ExamBoard(models.Model):
    def __unicode__(self):
       return self.board_name
       
    class Meta:
        ordering = ('board_name',)
       
    board_name = models.CharField('Exam Board Name', max_length = 200)
    pub_date = models.DateTimeField('Date published')
    

class ExamLevel(models.Model):
    def __unicode__(self):
       return self.level_name
       
    class Meta:
        ordering = ('level_number','level_name')
       
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
    level_name = models.CharField('Exam Level', max_length = 200)
    country = models.CharField('Country', max_length = 200, default = 'Any')
    level_number = models.CharField(
        max_length = 1,
        choices = YEAR_IN_SCHOOL_CHOICES,
        default = NONE
    )
    pub_date = models.DateTimeField('Date published')
    

class Syllabus(models.Model):
    def __unicode__(self):
        # if we have situations like IB IB, shorten to IB
        # if we have a subject name set (e.g. Computing not Computer Science),
        # show that, otherwise default to the subject
        if str(self.exam_level) == str(self.exam_board):
            if not self.subject_name:
                return str(self.exam_board) + ' ' + str(self.subject)
            else:
                return str(self.exam_board) + ' ' + str(self.subject_name)
        else:
            if not self.subject_name:
                return (
                    str(self.exam_board) + ' ' + 
                    str(self.subject) +  ' ' +
                    str(self.exam_level)
                )
            else:
                return (
                    str(self.exam_board) + ' ' + 
                    str(self.subject_name) +  ' ' +
                    str(self.exam_level)
                )
            
    class Meta:
        ordering = ('exam_board','exam_level')
        
    subject = models.ForeignKey(Subject)
    exam_board = models.ForeignKey(ExamBoard)
    exam_level = models.ForeignKey(ExamLevel)
    subject_name = models.CharField(
        max_length = 200,
        help_text = ('If the subject name is as above, leave blank otherwise ' +
            'enter correct name, e.g. Computing or Further Maths'),
        blank = True,
        null = True
    )
    pub_date = models.DateTimeField('Date published')
    
    
class Unit(models.Model):
    def __unicode__(self):
       return str(self.title)
       
    class Meta:
        ordering = ('title',)
       
    title = models.CharField(max_length = 200)
    syllabus = models.ForeignKey(Syllabus)
    description = models.TextField(
        blank = True, 
        null = True, 
        help_text = 'A brief overview of the content'
    )
    pub_date = models.DateTimeField('Date published')
    
    
        
class Topic(models.Model):
    def __unicode__(self):
       return str(self.title) 
       
    class Meta:
        ordering = ('title',)
        
    title = models.CharField(max_length = 200)
        
    
class UnitTopic(models.Model):
    def __unicode__(self):
       return str(self.title)
       
    class Meta:
        ordering = ('title',)
        
    title = models.CharField(max_length = 200)
    unit = models.ForeignKey(Unit)
    topic = models.ManyToManyField(Topic, blank = True, null = True)
    description = models.TextField(
        blank = True, 
        null = True, 
        help_text = 'E.g. the expected topics taught'
    )
    pub_date = models.DateTimeField('Date published')
    
    
class Licence(models.Model):
    def __unicode__(self):
       return str(self.name)
       
    name = models.CharField(max_length = 200)
    description = models.TextField(null = True)
    link = models.CharField('URL', max_length = 200)
    
      
class File(models.Model):
    def __unicode__(self):
        return self.filename
        
    filename = models.CharField('Filename', max_length = 200)
    file = models.FileField()
    mimetype = models.CharField('Mimetype', max_length = 200)
    filesize = models.IntegerField()
    pub_date = models.DateTimeField(
        'Date published', 
        auto_now_add = True, 
        blank = True
    )
    

class Resource(models.Model):
    def __unicode__(self):
       return str(self.title)
       
    class Meta:
        ordering = ('title',)
       
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
    search_fields = ['title', 'approved']
    title = models.CharField(max_length = 200)
    description = models.TextField('Description', null = True)
    file = models.ForeignKey(File, blank = True, null = True)
    link = models.CharField(max_length=400, blank = True, null = True)
    type = models.IntegerField(max_length=2, default=1, choices = RESOURCE_TYPES)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    author = models.CharField(
        'Author', 
        max_length = 200, 
        null = True,
        help_text='Who is the original author? E.g. John Smith. If you are ' + 
            'the author, write "me"'
    )
    author_link = models.CharField(
        'Author Link', 
        max_length = 200, 
        blank = True,
        null = True, 
        help_text='A URL or email to credit the original author. If it is ' +
            'you, leave blank'
    )
    #Don't really need but its for the forms, FIXME?
    subject = models.ForeignKey(Subject)
    syllabus = models.ForeignKey(Syllabus)
    unit = models.ForeignKey(Unit,  null = True, blank = True)
    unittopic = models.ForeignKey(
        UnitTopic, 
        null = True, 
        blank = True, 
        verbose_name = "Unit Topic"
    )
    topics = models.ManyToManyField(Topic, null = True, blank = True)
    licence = models.ForeignKey(
        Licence, 
        null = True, 
        help_text = mark_safe('<a href="uploader/licences/">Help with the ' + 
            'licences</a>')
        )

    approved = models.BooleanField(default=False)
    pub_date = models.DateTimeField(
        'Date published', 
        auto_now_add = True, 
        blank = True
    )
    
        
class Rating(models.Model):
    def __unicode__(self):
       return str(self.resource) + ': ' + str(self.rating)
       
    class Meta:
        ordering = ('pub_date',)
        
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
    rating = models.IntegerField(max_length = 1, choices = RATING_CHOICES)
    pub_date = models.DateTimeField(auto_now_add = True, blank = True)
   
   
class UserProfile(models.Model):
    def __unicode__(self):
       return str(self.user)
       
    class Meta:
        ordering = ('user',)
        
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    score = models.IntegerField(default = 0)
    
    
class Message(models.Model):
    def __unicode__(self):
       return str(self.message)
       
    class Meta:
        ordering = ('pub_date',)
        
    PM = 1
    ANNOUNCE = 2
    STICKY = 3

    MESSAGE_TYPE = (
        (PM, 'PrivateMessage'),
        (ANNOUNCE, 'Announcement'),
        (STICKY, 'Sticky')
    )
    
    message = models.TextField()
    user_from = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name = 'message_user_from'
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='message_user_to',
        null=True,
        blank=True
    )
    type = models.IntegerField(max_length = 1, choices = MESSAGE_TYPE)
    read = models.BooleanField(default = False)
    read_date = models.DateTimeField(null=True, blank=True)
    sticky_date = models.DateTimeField(null = True)
    pub_date = models.DateTimeField(auto_now_add = True)

# cleans up files from AWS when resource is deleted from DB
@receiver(pre_delete, sender=File)
def mymodel_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


    
    


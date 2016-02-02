from __future__ import division

import logging
import os
import pytz

from django.core.urlresolvers import reverse
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Avg
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe

logging.basicConfig()
logger = logging.getLogger(__name__)


class Subject(models.Model):
    subject_name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return self.subject_name

    class Meta:
        ordering = ('subject_name',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'active', 'pub_date')
    prepopulated_fields = {'slug': ('subject_name',)}


class ExamLevel(models.Model):
    NONE = '0'
    KS1 = '1'
    KS2 = '2'
    KS3 = '3'
    KS4 = '4'
    KS5 = '5'

    YEAR_IN_SCHOOL_CHOICES = (
        (NONE, 'None'),
        (KS1, 'KS1'),
        (KS2, 'KS2'),
        (KS3, 'KS3'),
        (KS4, 'KS4'),
        (KS5, 'KS5'),
    )
    level_name = models.CharField('Exam Level', max_length=200)
    country = models.CharField(
        max_length=200,
        default='Any',
        help_text='This is free text, so please check spelling and caps'
    )
    level_number = models.CharField(
        max_length=1,
        choices=YEAR_IN_SCHOOL_CHOICES,
        default=NONE
    )
    slug = models.SlugField(max_length=100, unique=True)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return self.level_name

    class Meta:
        ordering = ('country', 'level_number', 'level_name')


class ExamLevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'country', 'level_number', 'pub_date')
    prepopulated_fields = {"slug": ("level_name",)}


class Unit(models.Model):
    title = models.CharField(max_length=200)
    order = models.IntegerField(null=True, blank=True,
                                help_text='Use to correctly order units')
    syllabus = models.ForeignKey(Syllabus)
    description = models.TextField(
        blank=True,
        null=True,
        help_text='A brief overview of the content'
    )
    slug = models.SlugField(max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)
        unique_together = ('syllabus', 'slug')


class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'syllabus', 'description', 'slug', 'pub_date')
    list_filter = ('syllabus__subject', 'syllabus')
    prepopulated_fields = {"slug": ("title",)}


class Topic(models.Model):
    title = models.CharField(max_length=200)

    def __unicode__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)


class TopicAdmin(admin.ModelAdmin):
    list_display = ('title',)


class UnitTopic(models.Model):
    title = models.CharField(max_length=200)
    unit = models.ForeignKey(Unit)
    topic = models.ManyToManyField(Topic, blank=True, null=True)
    section = models.CharField(max_length=100, blank=True, null=True,
                               help_text='Use this to group topics by section')
    section_description = models.TextField(blank=True, null=True,
                                           help_text='A hacky way of showing some guidance for a section as it ' +
                                           'doesn\'t have a page itself')
    description = models.TextField(
        blank=True,
        null=True,
        help_text='E.g. the expected topics taught'
    )
    slug = models.SlugField(max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('title',)
        unique_together = ('unit', 'slug')
        
    def get_absolute_url(self):
        return reverse('uploader:unit_topic', 
            args=[self.unit.syllabus.subject.slug, self.unit.syllabus.exam_level.slug,
                  self.unit.syllabus.slug, self.unit.slug, self.slug])


class UnitTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'description', 'pub_date')
    list_filter = ('unit__syllabus__subject', 'unit__syllabus', 'unit')
    prepopulated_fields = {"slug": ("section", "title",)}


class Note(models.Model):
    unit_topic = models.OneToOneField(UnitTopic)
    content = models.TextField()
    slug = models.SlugField(
        unique=True,
        max_length=100)  # don't use this yet but may in future
    code = models.SlugField(max_length=4, unique=True)
    locked = models.BooleanField(default=False)
    locked_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)
    locked_at = models.DateTimeField(blank=True, null=True)
        
    def get_absolute_url(self):
        return reverse('uploader:view_notes_code', args=[self.code])
        
    def rating(self):
        votes = Vote.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(self)).aggregate(average=Avg('vote'))
        if votes['average'] is None:
            votes['average'] = 3.0        
        return votes['average']
        
    def __unicode__(self):
        return self.unit_topic.title
        

class NoteHistory(models.Model):
    note = models.ForeignKey(Note)
    type = models.CharField(max_length=4, choices=(('full', 'full'), ('diff', 'diff')))
    content = models.TextField()
    parent = models.ForeignKey('self', null=True, blank=True)
    comment = models.CharField(max_length=300, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    pub_date = models.DateTimeField(auto_now_add=True)


class NoteHistoryAdmin(admin.ModelAdmin):
    list_display = ('note', 'type', 'comment', 'user')
    

class NoteAdmin(admin.ModelAdmin):
    list_display = ('unit_topic', 'content')
    prepopulated_fields = {"slug": ("unit_topic",)}


class Licence(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(null=True)
    link = models.URLField('URL', max_length=200, null=True, blank=True)

    def __unicode__(self):
        return str(self.name)

    class Meta:
        ordering = ('name',)


class LicenceAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'link')


class File(models.Model):
    PRESENTATION = 1
    TASK = 2
    LESSON_PLAN = 3
    SOW = 4
    INFO = 5
    OTHER = 6

    FILE_TYPES = (
        (PRESENTATION, 'A lesson presentation'),
        (TASK, 'A lesson task'),
        (LESSON_PLAN, 'A lesson plan'),
        (SOW, 'A scheme of work'),
        (INFO, 'An informational document'),
        (OTHER, 'Other')
    )
    title = models.CharField(max_length=200)
    filename = models.CharField(max_length=200)
    file = models.FileField(upload_to='%Y/%m', blank=True)
    mimetype = models.CharField(max_length=200)
    filesize = models.IntegerField()
    description = models.TextField('Description', null=True)
    type = models.IntegerField(max_length=2, default=1, choices=FILE_TYPES)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True)
    uploader_is_author = models.BooleanField('Uploader is author?', default=True,
                                             help_text='Check if you are the author of the file')
    author = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='If you are not the author, please give credit where ' +
        'possible, some licences require it'
    )
    author_link = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text='An optional URL to link to credit an author'
    )
    licence = models.ForeignKey(
        Licence,
        null=True,
        # FIXME hard-coded
        help_text=mark_safe(
            '<br />When submitting your work, you need to choose how you ' +
            'want people to use it. If submitting others\', you must respect' +
            ' any existing licences. (<strong>Attribution-NonCommercial-' +
            'ShareAlike</strong> is a safe bet for new resources) ' +
            '<a href="/licences/">Still unsure?</a> ')
    )
    #topics = TaggableManager()
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField(
        'Date published',
        auto_now_add=True,
        blank=True
    )

    def __unicode__(self):
        return self.filename

    class Meta:
        ordering = ('-pub_date',)


class FileAdmin(admin.ModelAdmin):
    list_display = ('filename', 'title', 'file', 'mimetype', 'filesize',
                    'pub_date')
    prepopulated_fields = {"slug": ("title",)}


class Bookmark(models.Model):
    GENERAL = 'general'
    NEWS = 'news'
    VIDEO = 'video'
    INFO = 'info'
    BLOG = 'blog'
    IMAGE = 'image'

    BOOKMARK_TYPES = (
        (GENERAL, 'A website'),
        (NEWS, 'A news article'),
        (VIDEO, 'A video'),
        (INFO, 'An informational source, e.g. Wikipedia'),
        (BLOG, 'A blog'),
        (IMAGE, 'An image')
    )

    title = models.CharField(max_length=200)
    link = models.URLField(max_length=400)
    description = models.TextField(null=True)
    type = models.CharField(
        max_length=7,
        choices=BOOKMARK_TYPES,
        default='general')
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True)
    screenshot = models.CharField(max_length=300,
        null=True,
        blank=True)
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField(
        'Date published',
        auto_now_add=True,
        blank=True
    )

    def __unicode__(self):
        return self.title

    class Meta:
        ordering = ('-pub_date',)


class BookmarkAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'uploader', 'pub_date')
    prepopulated_fields = {"slug": ("title",)}


class Resource(models.Model):
    file = models.ForeignKey(File, blank=True, null=True)
    bookmark = models.ForeignKey(Bookmark, blank=True, null=True)
    uploader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True)
    # Don't really need but its for the forms, FIXME?
    subject = models.ForeignKey(Subject)
    # TODO do we really need a syllabus?
    syllabus = models.ForeignKey(Syllabus)
    unit = models.ForeignKey(Unit, null=True, blank=True)
    unit_topic = models.ForeignKey(
        UnitTopic,
        null=True,
        blank=True,
    )
    approved = models.BooleanField(default=False)
    code = models.SlugField(max_length=4, unique=True, null=True, blank=True)
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField(
        'Date published',
        auto_now_add=True,
        blank=True
    )

    def __unicode__(self):
        if self.file is not None:
            return str(self.file.title)
        elif self.bookmark is not None:
            return str(self.bookmark.title)
        else:
            return "File a bug: NoTitle(" + str(self.id) + ")"

    class Meta:
        ordering = ('-pub_date',)
        unique_together = ('file', 'bookmark', 'subject', 'syllabus', 'unit', 'unit_topic')

    def title(self):
        return str(self.file.title) if self.file else str(self.bookmark.title)

    def description(self):
        return self.file.description if self.file else self.bookmark.description
        
    def url(self):
        return self.file.filename if self.file else self.bookmark.link
    
    def get_absolute_url(self):
        return reverse('uploader:view_resource', args=[self.slug])
        
    def rating(self):
        votes = Vote.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(self)).aggregate(average=Avg('vote'))
        if votes['average'] is None:
            votes['average'] = 3.0
        return votes['average']
        
    def type(self):
        if self.bookmark:
            return 'bookmark'
        else:
            return 'file'


class ResourceAdmin(admin.ModelAdmin):
    list_display = ('file', 'slug', 'bookmark', 'uploader', 'subject', 'syllabus',
                    'unit', 'unit_topic', 'approved', 'pub_date')
    list_filter = ('approved',)
    actions = ['approve']

    def approve(self, request, queryset):
        rows_updated = queryset.update(approved=True)
        if rows_updated == 1:
            message_bit = "1 resource was"
        else:
            message_bit = "%s resources were" % rows_updated
        # FIXME message_user doesn't work
        self.message_user(request, "%s successfully approved." % message_bit)


class Vote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    vote = models.IntegerField(
        max_length=1, choices=(
            (0, "0 - Useless"), (1, "1 - Very Poor"), (2, "2 - Poor"), (3, "3 - Okay"), (4, "4 - Useful"), (5, '5 - Amazing')))
    pub_date = models.DateTimeField(auto_now_add=True, blank=True)

    class Meta:
        unique_together = ['user', 'content_type', 'object_id']


class TeacherProfile(models.Model):
    TITLES = (
        ('Mr', 'Mr'),
        ('Mrs', 'Mrs'),
        ('Miss', 'Miss'),
        ('Ms', 'Ms'),
        ('Dr', 'Dr'),
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, parent_link=True)
    title = models.CharField(max_length='7', choices=TITLES)
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject, null=True, blank=True)
    score = models.IntegerField(default=0)
    timezone = models.CharField(max_length=100, default='UTC')

    def __unicode__(self):
        return unicode(self.title + ' ' + self.surname)


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, parent_link=True)
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject, null=True, blank=True)
    score = models.IntegerField(default=0)
    timezone = models.CharField(max_length=100, default='UTC')


    def __unicode__(self):
        return unicode(self.forename + ' ' + self.surname)


class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'user')


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')





class Image(models.Model):
    image = models.ImageField(upload_to='images/%Y/%m')
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True)
    credit = models.CharField(max_length=300, blank=True, null=True,
                              help_text='Give credit if required')
    licence = models.ForeignKey(Licence)
    height = models.PositiveIntegerField(blank=True, null=True)
    width = models.PositiveIntegerField(blank=True, null=True)
    code = models.SlugField(max_length=4, unique=True)
    alt_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField(auto_now_add=True)
    




######## signals TODO move to own file #########

# cleans up files from AWS when resource is deleted from DB


@receiver(pre_delete, sender=File)
def mymodel_delete(sender, instance, **kwargs):
    instance.file.delete(False)

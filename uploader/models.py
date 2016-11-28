from __future__ import division

import logging
import os

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

    def __str__(self):
        return self.subject_name

    class Meta:
        ordering = ('subject_name',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'active', 'pub_date')
    prepopulated_fields = {'slug': ('subject_name',)}


class ExamBoard(models.Model):
    board_name = models.CharField('Exam Board Name', max_length=200)
    pub_date = models.DateTimeField('Date published')

    def __str__(self):
        return self.board_name

    class Meta:
        ordering = ('board_name',)


class ExamBoardAdmin(admin.ModelAdmin):
    list_display = ('board_name', 'pub_date')


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

    def __str__(self):
        return self.level_name

    class Meta:
        ordering = ('country', 'level_number', 'level_name')


class ExamLevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'country', 'level_number', 'pub_date')
    prepopulated_fields = {"slug": ("level_name",)}


class Syllabus(models.Model):
    subject = models.ForeignKey(Subject)
    exam_board = models.ForeignKey(ExamBoard)
    exam_level = models.ForeignKey(ExamLevel)
    subject_name = models.CharField(
        max_length=200,
        help_text=('If the subject name is as above, leave blank otherwise ' +
                   'enter correct name, e.g. Computing or Further Maths'),
        blank=True,
        null=True
    )
    description = models.TextField(null=True, blank=True)
    official_site = models.URLField(max_length=200, null=True, blank=True)
    teach_from = models.DateField(
        null=True,
        blank=True,
        help_text='Date of first teaching')
    teach_until = models.DateField(
        null=True,
        blank=True,
        help_text='Date of last teaching')
    slug = models.SlugField(max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __str__(self):
        # Fix for BTEC and IB oddities as the qualification and exam board
        # are the same and read badly
        if ('BTEC' in str(self.exam_board) or
                'Baccalaureate' in str(self.exam_board) or
                'National Curriculum' in str(self.exam_board)):
            first_part = str(self.exam_board) + " " + \
                str(self.subject_name or self.subject)
        else:
            first_part = str(self.exam_board) + " " + str(self.subject_name or
                                                          self.subject) + " " + str(self.exam_level)

        if self.teach_from is not None:
            return str(first_part) + " (" + str(
                self.teach_from.strftime("%Y")) + ")"
        else:
            return str(first_part)

    class Meta:
        ordering = ('exam_board', 'exam_level', 'subject')
        verbose_name_plural = "Syllabuses"
        unique_together = ('subject', 'exam_board', 'exam_level', 'slug')


class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('subject', 'exam_board', 'exam_level', 'subject_name',
                    'pub_date')


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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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
        
    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
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

    def __str__(self):
        return str(self.title + ' ' + self.surname)


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, parent_link=True)
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject, null=True, blank=True)
    score = models.IntegerField(default=0)
    timezone = models.CharField(max_length=100, default='UTC')


    def __str__(self):
        return (self.forename + ' ' + self.surname)


class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'score', 'user')


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')


class Message(models.Model):
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
        related_name='message_user_from'
    )
    user_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='message_user_to',
        null=True,
        blank=True
    )
    type = models.IntegerField(max_length=1, choices=MESSAGE_TYPE)
    read = models.BooleanField(default=False)
    read_date = models.DateTimeField(null=True, blank=True)
    sticky_date = models.DateTimeField(null=True)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.message)

    class Meta:
        ordering = ('-pub_date',)


class MessageAdmin(admin.ModelAdmin):
    list_display = ('message', 'user_from', 'user_to', 'type', 'read',
                    'read_date', 'sticky_date', 'pub_date')


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
    
    
class ImageAdmin(admin.ModelAdmin):
    list_display = ('image', 'credit', 'licence', 'code', 'alt_text')


class Question(models.Model):
    unit_topic = models.ForeignKey(UnitTopic)
    text = models.TextField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        
    def rating(self):
        votes = Vote.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(self)).aggregate(average=Avg('vote'))
        if votes['average'] is None:
            votes['average'] = 3.0
        return votes['average']


class MultipleChoiceQuestion(Question):
    number_of_options = models.IntegerField(
        choices=(
            (2, "2"), (3, "3"), (4, "4")))
    answer = models.IntegerField(
        choices=(
            (1, "1"), (2, "2"), (3, "3"), (4, "4")))

    def __str__(self):
        return str(self.text)


class Answer(models.Model):

    class Meta:
        abstract = True


class MultipleChoiceAnswer(Answer):
    question = models.ForeignKey(MultipleChoiceQuestion)
    text = models.CharField(max_length=300)
    number = models.IntegerField()

    def __str__(self):
        return self.text


class Group(models.Model):
    name = models.CharField(max_length='100')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL)
    year = models.CharField(max_length='3', help_text='E.g. 7, 12, FS1', null=True, blank=True)
    subject = models.ForeignKey(Subject, null=True, blank=True)
    code = models.SlugField(max_length='4', unique=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    
    def unmarked_assignments(self):
        return AssignmentSubmission.objects.filter(status=1, assignment__group=self).count()

    class Meta:
        unique_together = ["name", "teacher"]

    def __str__(self):
        return self.name


class Test(models.Model):
    subject = models.ForeignKey(Subject)
    syllabus = models.ForeignKey(Syllabus, blank=True, null=True)
    unit = models.ForeignKey(Unit, blank=True, null=True)
    unit_topic = models.ForeignKey(UnitTopic, blank=True, null=True)
    public = models.BooleanField(default=False)
    use_own_questions = models.BooleanField(default=False,
                                            help_text='Coming soon')
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True)
    group = models.ForeignKey(Group)
    code = models.SlugField(max_length='5', unique=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)
    total = models.IntegerField(default=10, help_text='If the total is ' +
                                ' greater than the number of available questions, it will be changed')

    def __str__(self):
        rep = None
        if self.unit_topic:
            rep = self.unit_topic
        elif self.unit:
            rep = self.unit
        elif self.syllabus:
            rep = self.syllabus

        return (rep)

    class Meta:
        ordering = ('-deadline', '-pub_date')
        
    def rating(self):
        votes = Vote.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(self)).aggregate(average=Avg('vote'))
        if votes['average'] is None:
            votes['average'] = 3.0        
        return votes['average']


class UserAnswer(models.Model):
    test = models.ForeignKey(Test)
    question = models.ForeignKey(MultipleChoiceQuestion)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    answered = models.DateTimeField(auto_now_add=True)
    correct = models.BooleanField(default=False)

    class Meta:
        abstract = True
        unique_together = (("user", "question"),)


class MultipleChoiceUserAnswer(UserAnswer):
    answer_chosen = models.ForeignKey(MultipleChoiceAnswer)

    def question(self):
        return super.question
    question.short_name = "Question"

    def user(self):
        return super.user
    user.short_name = "User"

    def answered(self):
        return super.answered
    answered.short_name = "Answered"

    def correct(self):
        return super.correct
    correct.short_name = "Correct"


class MultipleChoiceUserAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'user', 'correct', 'answered',
                    'answer_chosen')


class StudentGroup(models.Model):
    group = models.ForeignKey(Group)
    student = models.ForeignKey(settings.AUTH_USER_MODEL)
    joined = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["group", "student"]


class TestResult(models.Model):
    test = models.ForeignKey(Test, blank=True, null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    taken = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField()


class Lesson(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=100)
    code = models.SlugField(unique=True, max_length=4, null=True, blank=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    objectives = models.TextField(blank=True, null=True)
    pre_post = models.BooleanField(default=False)
    public = models.BooleanField(default=True, blank=True)
    presentation = models.FileField(upload_to='%Y/%m', null=True, blank=True)
    show_presentation_to_students = models.BooleanField(default=False)
    unit_topic = models.ForeignKey(UnitTopic, null=True, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
        
    def rating(self):
        votes = Vote.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(self)).aggregate(average=Avg('vote'))
        if votes['average'] is None:
            votes['average'] = 3.0        
        return votes['average']


class LessonItem(models.Model):
    lesson = models.ForeignKey(Lesson)
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    order = models.PositiveIntegerField()
    instructions = models.TextField(blank=True, null=True)


class LessonItemAdmin(admin.ModelAdmin):
    list_display = ('lesson', 'content_type', 'object_id', 'order')


class LessonPrePost(models.Model):
    group_lesson = models.ForeignKey('GroupLesson')
    text = models.CharField(max_length=255)
    
    def __str__(self):
        return self.text


class LessonPrePostResponse(models.Model):
    pre_post = models.ForeignKey(LessonPrePost)
    type = models.CharField(max_length=4)
    student = models.ForeignKey(settings.AUTH_USER_MODEL)
    score = models.IntegerField(choices=((1, "1"), (2, "2"), (3, "3"), 
                                         (4, "4"), (5, "5")))
    pub_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('pre_post', 'type', 'student')


class LessonPrePostResponseAdmin(admin.ModelAdmin):
    list_display = ('pre_post', 'type', 'student', 'score')
    

class Favourite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class SyllabusFavourite(Favourite):
    syllabus = models.ForeignKey(Syllabus)

    class Meta:
        unique_together = ["user", "syllabus"]


class UnitFavourite(Favourite):
    unit = models.ForeignKey(Unit)

    class Meta:
        unique_together = ["user", "unit"]


class UnitTopicFavourite(Favourite):
    unit_topic = models.ForeignKey(UnitTopic)

    class Meta:
        unique_together = ["user", "unit_topic"]


class UnitTopicLink(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    unit_topic_1 = models.ForeignKey(UnitTopic)
    unit_topic_2 = models.ForeignKey(UnitTopic, related_name='unit_topic_2')
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["unit_topic_1", "unit_topic_2"]
        
        
class GroupLesson(models.Model):
    group = models.ForeignKey(Group)
    lesson = models.ForeignKey(Lesson)
    set_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    pub_date = models.DateTimeField(auto_now_add=True)
    date = models.DateField(null=True, blank=True)
    period = models.IntegerField(null=True, blank=True, choices=(
         (1, "P1"), (2, "P2"), (3, "P3"), (4, "P4"), (5, "P5"), (6, "P6")))
         
    def __str__(self):
        return str(self.group) + " | " + str(self.lesson)
    


class GradeSystem(models.Model):
    pass


class Assignment(models.Model):
    title = models.CharField(max_length=255)
    code = models.SlugField(unique=True)
    group = models.ForeignKey(Group)
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL)
    deadline = models.DateTimeField()
    description = models.TextField()
    unit_topic = models.ForeignKey(UnitTopic, blank=True, null=True)
    total = models.PositiveIntegerField(blank=True, null=True)
    comments_only = models.BooleanField(default=False)
    offline = models.BooleanField(default=False, help_text='Students will not submit anything before entering marks, e.g. paper-based activity or test')
    grading = models.ForeignKey('Grading', blank=True, null=True)
    public = models.BooleanField(default=False)
    pub_date = models.DateTimeField(auto_now_add=True)

    def unmarked(self):
        return AssignmentSubmission.objects.filter(status=1, assignment=self).count()
        
    def rating(self):
        votes = Vote.objects.filter(object_id=self.id, content_type=ContentType.objects.get_for_model(self)).aggregate(average=Avg('vote'))
        if votes['average'] is None:
            votes['average'] = 3.0        
        return votes['average']

def assignment_location(instance, filename):
        code = instance.assignment_submission.assignment.code
        
        return '/'.join(['assignments', code, filename])


class AssignmentSubmissionFile(models.Model):
    assignment_submission = models.ForeignKey('AssignmentSubmission')
    comments = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to=assignment_location)
    pub_date = models.DateTimeField(auto_now_add=True)
    
    def filename(self):
        return os.path.basename(self.file.name)

    
class AssignmentSubmission(models.Model):
    UNMARKED = 1
    MARKED = 2
    NEEDSIMP = 3
    INCOMP = 4
    ABSENT = 5

    FEEDBACK_STATUS = (
        (UNMARKED, 'Unmarked'),
        (MARKED, 'Marked'),
        (NEEDSIMP, 'Needs improvement'),
        (INCOMP, 'Incomplete'),
        (ABSENT, 'Absent')
    )
    assignment = models.ForeignKey(Assignment)
    student = models.ForeignKey(settings.AUTH_USER_MODEL)
    feedback = models.TextField(blank=True, null=True)
    result = models.IntegerField(blank=True, null=True)
    feedback_file = models.FileField(upload_to=assignment_location, blank=True, null=True)
    status = models.IntegerField(choices=FEEDBACK_STATUS, default=UNMARKED)
    audio_feedback = models.FileField(upload_to=assignment_location, blank=True, null=True)
    submitted = models.DateTimeField(auto_now_add=True)
    marked = models.DateTimeField(auto_now=True, null=True, blank=True)
    
    def percentage(self):
        if self.assignment.grading.type == 1:
            return int(self.result / self.assignment.total * 100)
        else:
            return None
    
    def percentage_string(self):
        if self.assignment.grading.type == 1:
            return str(self.percentage()) + "%"
        else:
            return None
    
    def numerical_grade_value(self):
        if self.assignment.grading.type == 1:
            percentage = self.percentage()
                
            boundaries = NumericalGrade.objects.filter(grading=self.assignment.grading)
            
            i = 0
            grade = None
            for boundary in boundaries:
                logger.error("Comparing " + str(percentage) + " to " + str(boundary.upper_bound))
                if percentage >= boundary.upper_bound:
                    grade = boundaries[i-1].grade
                    break
                elif (i + 1) == len(boundaries): # last run, bottom grade
                    grade = boundaries[i].grade
                i += 1
            return grade
        else:
            return None
    
    def grade(self):
        if self.assignment.grading.type == 2:
            return GradeOptions.objects.get(
                grading=self.assignment.grading,
                value=self.result).grade
        elif self.assignment.grading.type == 1:
            percentage = self.percentage()
            grade = self.numerical_grade_value()
                
            return str(grade)  
            
    def grade_type(self):
        if self.assignment.grading.type == 2:
            return GradeOptions.objects.get(
                grading=self.assignment.grading,
                value=self.result).hi_med_lo
        else:
            type = 'fail'
            percentage = self.percentage()
            if percentage > 80:
                type = 'hi'
            elif percentage > 60:
                type = 'med'
            elif percentage > 40:
                type = 'lo'
            
            return type
            
    def on_time(self):
        return self.submitted < self.assignment.deadline

                            
    
class Grading(models.Model):
    NUMERICAL = 1
    OPTIONS  = 2
    
    GRADING_TYPES = (
        (NUMERICAL, 'Numerical grade scale'),
        (OPTIONS, 'Pre-set grade options'))
    
    title = models.CharField(max_length=200)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    description = models.TextField(null=True, blank=True)
    type = models.PositiveIntegerField(max_length=1, choices=GRADING_TYPES, default=0)
    public = models.BooleanField(default=False)
    pub_date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.public:
            grading = "[Public] "
        else:
            grading = "[User] "

        grading += str(self.title)
            
        if self.description:
            grading +=  str(': ') + str(self.description)
        
        grading += " (" + str(self.get_type_display()) + ")"
        return grading
        
    class Meta:
        ordering = ('-public', 'title')
    
    
    
class GradeOptions(models.Model):
    grading = models.ForeignKey(Grading, null=True, blank=True)
    value = models.PositiveIntegerField()
    hi_med_lo = models.CharField(max_length=4, choices=(
        ('hi', 'High'), ('med', 'Medium'), ('lo', 'Low'), ('fail', 'Fail')), 
        help_text='What level grade is this classified as? Used to colour code the grades, not displayed.',
        blank=True, null=True)
    grade = models.CharField(max_length=50)
    grade_long = models.TextField(null=True, blank=True)
    order = models.PositiveIntegerField()
    pub_date = models.DateTimeField(auto_now_add=True)
 
    
class NumericalGrade(models.Model):
    grading = models.ForeignKey(Grading, null=True, blank=True)
    upper_bound = models.PositiveIntegerField(help_text='As a percentage')
    grade = models.CharField(max_length=10)
    grade_long = models.TextField(null=True, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)


######## signals TODO move to own file #########

# cleans up files from AWS when resource is deleted from DB


@receiver(pre_delete, sender=File)
def mymodel_delete(sender, instance, **kwargs):
    instance.file.delete(False)

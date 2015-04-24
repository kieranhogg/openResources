import logging

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
#from taggit_autosuggest.managers import TaggableManager

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


class ExamBoard(models.Model):
    board_name = models.CharField('Exam Board Name', max_length=200)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
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

    def __unicode__(self):
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
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
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
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)


class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'syllabus', 'description', 'pub_date')
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
    slug = models.SlugField(unique=True, max_length=100)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)


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
        
    def get_absolute_url(self):
        return reverse('note', kwargs={'slug': self.unit_topic.slug})


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
    screenshot = models.ImageField(
        upload_to='screenshots/%Y/%m',
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

    def get_title(self):
        return self.file.title if self.file else self.bookmark.title

    def get_description(self):
        return self.file.description if self.file else self.bookmark.description
    
    def get_absolute_url(self):
        return reverse('resource', kwargs={'slug': self.slug})


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


class Rating(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    resource = models.ForeignKey(Resource)
    rating = models.IntegerField(
        max_length=1, choices=(
            (0, "0"), (1, "1"), (2, "2"), (3, "3"), (4, "4"), (5, '5')))
    pub_date = models.DateTimeField(auto_now_add=True, blank=True)

    def __unicode__(self):
        return str(self.resource) + ': ' + str(self.get_rating_display())

    class Meta:
        # ordering = ('-pub_date',)
        unique_together = ["user", "resource"]


class RatingAdmin(admin.ModelAdmin):
    list_display = ('resource', 'rating', 'user', 'pub_date')


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
    profile_setup = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.title + ' ' + self.surname)


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, parent_link=True)
    forename = models.CharField(max_length=100)
    surname = models.CharField(max_length=100)
    subjects = models.ManyToManyField(Subject, null=True, blank=True)
    score = models.IntegerField(default=0)
    profile_setup = models.BooleanField(default=False)

    def __unicode__(self):
        return unicode(self.forename + ' ' + self.surname)


class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'score')


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

    def __unicode__(self):
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
    pub_date = models.DateTimeField(auto_now_add=True)


class Question(models.Model):
    unit_topic = models.ForeignKey(UnitTopic)
    text = models.TextField()
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class MultipleChoiceQuestion(Question):
    number_of_options = models.IntegerField(
        choices=(
            (2, "2"), (3, "3"), (4, "4")))
    answer = models.IntegerField(
        choices=(
            (1, "1"), (2, "2"), (3, "3"), (4, "4")))

    def __unicode__(self):
        return str(self.text)


class Answer(models.Model):

    class Meta:
        abstract = True


class MultipleChoiceAnswer(Answer):
    question = models.ForeignKey(MultipleChoiceQuestion)
    text = models.CharField(max_length=300)
    number = models.IntegerField()

    def __unicode__(self):
        return self.text


class Group(models.Model):
    name = models.CharField(max_length='100')
    teacher = models.ForeignKey(settings.AUTH_USER_MODEL)
    slug = models.SlugField(unique=True, max_length='100')
    code = models.CharField(max_length='4', unique=True)
    pub_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["name", "teacher"]

    def __unicode__(self):
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
    code = models.CharField(max_length='5', unique=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(blank=True, null=True)
    total = models.IntegerField(default=10, help_text='If the total is ' +
                                ' greater than the number of available questions, it will be changed')

    def __unicode__(self):
        rep = None
        if self.unit_topic:
            rep = self.unit_topic
        elif self.unit:
            rep = self.unit
        elif self.syllabus:
            rep = self.syllabus

        return unicode(rep)

    class Meta:
        ordering = ('-deadline', '-pub_date')


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
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    objectives = models.TextField(blank=True, null=True)
    url = models.URLField()
    public = models.BooleanField(default=True, blank=True)
    presentation = models.FileField(upload_to='%Y/%m', null=True, blank=True)
    show_presentation_to_students = models.BooleanField(default=False)
    unit_topic = models.ForeignKey(UnitTopic, null=True, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return self.title


class LessonItem(models.Model):
    lesson = models.ForeignKey(Lesson)
    type = models.CharField(max_length=50)
    slug = models.SlugField(max_length=100, blank=True, null=True)
    order = models.IntegerField()
    instructions = models.TextField(blank=True, null=True)


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

######## signals TODO move to own file #########

# cleans up files from AWS when resource is deleted from DB


@receiver(pre_delete, sender=File)
def mymodel_delete(sender, instance, **kwargs):
    instance.file.delete(False)

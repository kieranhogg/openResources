from django.db import models
from django.conf import settings
from django.contrib import admin
from django.db.models.signals import pre_delete, post_save
from django.dispatch.dispatcher import receiver
from django.utils.safestring import mark_safe
from django.contrib.auth.models import User


class Subject(models.Model):
    subject_name = models.CharField(max_length=200)
    active = models.BooleanField(default=True)
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return self.subject_name

    class Meta:
        ordering = ('subject_name',)


class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'active', 'pub_date')


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
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return self.level_name

    class Meta:
        ordering = ('country', 'level_number', 'level_name')


class ExamLevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'country', 'level_number', 'pub_date')


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
    teach_from = models.DateField(null=True, blank=True, help_text='Date of first teaching')
    teach_until = models.DateField(null=True, blank=True, help_text='Date of last teaching')
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        if self.teach_from is not None:
            return str(self.exam_board) + " " + (str(self.subject_name) or 
                str(self.subject)) + " " + str(self.exam_level) + " (" + str(
                    self.teach_from.strftime("%Y")) + ")"
        else:
            return str(self.exam_board) + " " + (str(self.subject_name) or 
                str(self.subject)) + str(self.exam_level)
        
    class Meta:
        ordering = ('subject', 'exam_board', 'exam_level')
        verbose_name_plural = "Syllabuses"


class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('subject', 'exam_board', 'exam_level', 'subject_name',
                    'pub_date')


class Unit(models.Model):
    title = models.CharField(max_length=200)
    syllabus = models.ForeignKey(Syllabus)
    description = models.TextField(
        blank=True,
        null=True,
        help_text='A brief overview of the content'
    )
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)


class UnitAdmin(admin.ModelAdmin):
    list_display = ('title', 'syllabus', 'description', 'pub_date')


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
    description = models.TextField(
        blank=True,
        null=True,
        help_text='E.g. the expected topics taught'
    )
    pub_date = models.DateTimeField('Date published')

    def __unicode__(self):
        return str(self.title)

    class Meta:
        ordering = ('title',)


class UnitTopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'unit', 'description', 'pub_date')


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
    LESSON_PLAN = 2
    SOW = 3

    FILE_TYPES = (
        (PRESENTATION, 'A lesson presentation'),
        (LESSON_PLAN, 'A lesson plan'),
        (SOW, 'A scheme of work'),
    )
    title = models.CharField(max_length=200)
    filename = models.CharField(max_length=200)
    file = models.FileField(upload_to='%Y/%m')
    mimetype = models.CharField(max_length=200)
    filesize = models.IntegerField()
    description = models.TextField('Description', null=True)
    type = models.IntegerField(max_length=2, default=1, choices=FILE_TYPES)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
    author = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text='Who is the original author? E.g. John Smith. If you are ' +
                  'the author, write "me" if you are logged in, otherwise ' +
                  'add your name'
    )
    author_link = models.URLField(
        max_length=200,
        blank=True,
        null=True,
        help_text='A URL to credit the original author. If it is ' +
                  'you and you\'re logged in, leave blank'
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
    topics = models.ManyToManyField(Topic, null=True, blank=True)
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


class Bookmark(models.Model):
    title = models.CharField(max_length=200)
    link = models.URLField(max_length=400)
    description = models.TextField('Description', null=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
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


class Resource(models.Model):
    file = models.ForeignKey(File, blank=True, null=True)
    bookmark = models.ForeignKey(Bookmark, blank=True, null=True)
    uploader = models.ForeignKey(settings.AUTH_USER_MODEL)
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


class ResourceAdmin(admin.ModelAdmin):
    list_display = ('file', 'bookmark', 'uploader', 'subject', 'syllabus',
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

    def __unicode__(self):
        return str(self.resource) + ': ' + str(self.get_rating_display())

    class Meta:
        ordering = ('-pub_date',)
        unique_together = ["user", "resource"]


class RatingAdmin(admin.ModelAdmin):
    list_display = ('resource', 'rating', 'user', 'pub_date')


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    score = models.IntegerField(default=0)

    def __unicode__(self):
        return str(self.user)

    class Meta:
        ordering = ('user',)


class UserProfileAdmin(admin.ModelAdmin):
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
    
######## signals TODO move to own file #########

# cleans up files from AWS when resource is deleted from DB
@receiver(pre_delete, sender=File)
def mymodel_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)

# Creates user profile
@receiver(post_save, sender=User)
def user_post_save(sender, instance, **kwargs):
    # only fire if it's a new user not if we're saving an edit
    if kwargs['created']:
        profile = UserProfile()
        profile.user=instance
        profile.save()

#dispatcher.connect(user_post_save, signal=signals.post_save, sender=User)

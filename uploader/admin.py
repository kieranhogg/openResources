from django.contrib import admin
from uploader.models import *


# Register your models here.
admin.site.register(Syllabus, SyllabusAdmin)
admin.site.register(ExamBoard, ExamBoardAdmin)
admin.site.register(ExamLevel, ExamLevelAdmin)
admin.site.register(Subject, SubjectAdmin)
admin.site.register(Resource, ResourceAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(UnitTopic, UnitTopicAdmin)
admin.site.register(Topic, TopicAdmin)
admin.site.register(Licence, LicenceAdmin)
admin.site.register(File, FileAdmin)
admin.site.register(Rating, RatingAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
admin.site.register(Message, MessageAdmin)





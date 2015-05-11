import re

from django import template

from uploader.models import Subject

register = template.Library()


class IncludeNode(template.Node):
    def __init__(self, template_name):
        self.template_name = template_name

    def render(self, context):
        try:
            # Loading the template and rendering it
            included_template = template.loader.get_template(
                    self.template_name).render(context)
        except template.TemplateDoesNotExist:
            included_template = ''
        return included_template


@register.tag
def try_to_include(parser, token):
    """Usage: {% try_to_include "head.html" %}

    This will fail silently if the template doesn't exist. If it does, it will
    be rendered with the current context."""
    try:
        tag_name, template_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])

    return IncludeNode(template_name[1:-1])

@register.inclusion_tag('uploader/snippets/test_table.html')
def test_table(teacher_or_student, tests, group=None):
    return {'teacher_or_student': teacher_or_student, 'tests': tests}
    
    
@register.inclusion_tag('uploader/snippets/lesson_table.html')
def lesson_table(teacher_or_student, lessons, group=None):
    return {'teacher_or_student': teacher_or_student, 'lessons': lessons}
    

@register.inclusion_tag('uploader/snippets/assignment_table.html')
def assignment_table(teacher_or_student, assignments, group=None):
    return {'teacher_or_student': teacher_or_student, 'assignments': assignments, 'group': group}
    

@register.tag
def resource_icon(resource):
    if resource.type == 'bookmark':
        mapping = {
            'video': 'facetime-video',
            'news': 'list-alt',
            'image': 'image',
            'info': 'info-sign',
            'blog': 'comment',
            
        }
    
        icon = 'bookmark'
        if type in mapping:
            icon = mapping[type]
    
        html = '<span class="glyphicon glyphicon-{}" aria-hidden="true"></span>'
        html.format(icon)
    else:
        html = '<span class="glyphicon glyphicon-paperclip" aria-hidden="true"></span>'
    
    return html

@register.inclusion_tag('uploader/snippets/linking_embed.html')
def link_embed():
    subjects = Subject.objects.all()
    return {'subjects': subjects}


urlfinder = re.compile('^(http:\/\/\S+)')
urlfinder2 = re.compile('\s(http:\/\/\S+)')
@register.filter('urlify_markdown')
def urlify_markdown(value):
    value = urlfinder.sub(r'<\1>', value)
    return urlfinder2.sub(r' <\1>', value)
from django import template

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
def test_table(teacher_or_student, tests):
    return {'teacher_or_student': teacher_or_student, 'tests': tests}
    
    
@register.inclusion_tag('uploader/snippets/lesson_table.html')
def lesson_table(teacher_or_student, lessons):
    return {'teacher_or_student': teacher_or_student, 'lessons': lessons}
    

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

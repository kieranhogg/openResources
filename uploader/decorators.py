def is_teacher(user):
    if user:
        return user.groups.filter(name='teacher').count() == 1
    return False
def is_teacher(user):
    if user:
        return user.groups.filter(name='teacher').count() == 1
    return False
    
def is_student(user):
    if user:
        return user.groups.filter(name='student').count() == 1
    return False
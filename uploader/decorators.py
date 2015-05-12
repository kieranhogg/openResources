def is_teacher(user):
    if user:
        return user.groups.filter(name='teachers').count() == 1
    return False
    
def is_student(user):
    if user:
        return user.groups.filter(name='students').count() == 1
    return False
# coding: utf8
# try something like
def index(): return dict(message="hello from familysearch.py")

#################################
## custom FamilySearch functions
#################################

def apply():
    """
    Allows interested students to apply for the opportunity
    """
    form = SQLFORM(db.fs_prospects,fields = ['interested_location','interested_dates','language_level','referred_by','resume'])
    if form.process().accepted:
        response.flash = 'Thank you, we will keep you updated about this and future opportunities'
    elif form.errors:
        response.flash = 'There was an error on the form'
    else:
        response.flash = 'Welcome, please fill out the information below'
    return dict(form=form)

def register():
    """
    Allows approved prospects to register for their project
    """
    form = SQLFORM(db.fs_volunteers, fields = ['opp_location','internship','training_hotel','birthday','emergency_name','emergency_phone'])
    if form.process().accepted: #**** next=fsoverview - directs user to an overview page
        response.flash = 'Thank you, we will be making arrangements for your trip'
    elif form.errors:
        response.flash = 'There was an error on the form'
    else:
        response.flash = 'Welcome, please fill out the information below'
    return dict(form=form)

def volunteerupdate():
    """
    Allows administration to fill out or update additional information about the student
    """
    record = db.fs_volunteers(request.args(0)) or redirect(URL('index'))
    form = SQLFORM(db.fs_volunteers, record)
    if form.process(next='fsshowstudents').accepted:
        response.flash = 'Thank you, the student has been updated'
    elif form.errors:
        response.flash = 'There was an error on the form'
    else:
        response.flash = 'Please update the students info'
    return dict(form=form)

def showvolunteers():
    """
    Shows a list of all students
    **** need to figure out how to filter it
    """
    response.flash = 'Please choose a student to edit'
    query = (db.fs_volunteers)
    students = db(query).select()
    return dict(students = students)

def trackvolunteers():
    """
    shows a graph of a volunteers progress toward their departure
    """

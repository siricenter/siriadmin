# coding: utf8
# try something like
def index(): return dict(message="hello from mentorTrack.py")

def projects():
	count = db.mentorTrack_projects.project_name.count()
	projectList = db(db.mentorTrack_projects.project_name==db.siri_projects.id).select(db.siri_projects.name, count, groupby=db.mentorTrack_projects.project_name)
	
	userAlias = db.auth_user.with_alias('mentee_id')
	mentorAlias = db.auth_user.with_alias('mentor_id')
	mentorTrack_mentees = db((db.mentorTrack_mentees.project_name==db.siri_projects.id)&
		(db.mentorTrack_mentees.user_id==userAlias.id)&
		(db.mentorTrack_mentees.mentor_id==mentorAlias.id)).select(orderby=db.mentorTrack_mentees.project_name)

	buildProjectForm = SQLFORM(db.mentorTrack_projects)
	assignMentorTrackForm = SQLFORM(db.mentorTrack_mentees)
	return locals()


def mentees():

	return locals()


def editEntries():
	"""
	db.define_table('mentorTrack_mentees',
    Field('user_id', 'reference auth_user', label='Mentee', unique=True, requires=IS_IN_DB(db, db.auth_user.id, '%(first_name)s %(last_name)s')),
    Field('mentor_id', 'reference auth_user', label='Mentor', requires=IS_IN_DB(db, db.auth_user.id, '%(first_name)s %(last_name)s')),
    Field('project_name', 'reference siri_projects', requires=IS_IN_DB(db, db.siri_projects.id, '%(name)s')),
    format='%(user_id)s'
    #Field('project_id', 'reference mentorTrack_projects', requires=IS_IN_DB(db, db.mentorTrack_projects.id, '%(project_name)%'))
    )
	"""
	return locals()


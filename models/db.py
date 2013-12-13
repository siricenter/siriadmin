# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL('sqlite://storage.sqlite',pool_size=1,check_reserved=['all'])
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db=db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

# import gdata
# import gdata.docs.service
# import gspread
# import xlwt
# from xlwt import *
from datetime import datetime, date, time, timedelta, tzinfo
from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db)
crud, service, plugins = Crud(db), Service(), PluginManager()

## create all tables needed by auth if not custom tables
auth.define_tables(username=False, signature=False)

## configure email
mail = auth.settings.mailer
mail.settings.server = 'logging' or 'smtp.gmail.com:587'
mail.settings.sender = 'e.caldwell@sirinstitute.org'
mail.settings.login = 'dawg3tt:mol090901!'

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth, filename='private/janrain.key')

## this is the janrain login code for Facebook, Google, etc. login
## TODO: token URL not whitelisted
# from gluon.contrib.login_methods.rpx_account import RPXAccount
# auth.settings.actions_disabled=['register','change_password','request_reset_password']
# auth.settings.login_form = RPXAccount(request,
#     api_key='0caee29a1f349b43e83b5d1cb5cb5019eec2bef4',
#     domain='siri-admin',
#     url = "http://your-external-address/%s/default/user/login" % request.application)

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

# db questions: should the students all be in one complex table or should they be in separate tables?

db.define_table('timeclock',
    Field('project','string', required=True, label='Project'),
    Field('work_date','date', required=True, label='Work Date'),
    Field('time_in','time', required=True, label='Time In'),
    Field('time_in_ampm','string', required=True, label=''),
    Field('time_out','time', required=True, label='Time Out'),
    Field('time_out_ampm','string', required=True, label=''),
    Field('description', 'text', required=True, label='Description'),
    Field('hours','double', label='hours'),
    Field('usr_id','reference auth_user', label='ID', readable=False)
)
db.timeclock.project.requires = IS_IN_DB(db,'siri_projects.name')
db.timeclock.work_date.requires = IS_DATE(format='%m/%d/%Y')
db.timeclock.time_in.requires = IS_NOT_EMPTY()
db.timeclock.time_in_ampm.requires = IS_IN_SET(['AM', 'PM'])
db.timeclock.time_in_ampm.default = 'AM'
db.timeclock.time_out.requires = IS_NOT_EMPTY()
db.timeclock.time_out_ampm.requires = IS_IN_SET(['AM', 'PM'])
db.timeclock.time_out_ampm.default = 'PM'
db.timeclock.description.requires = IS_NOT_EMPTY()
# db.timeclock.hours.readable = False
db.timeclock.usr_id.writable = db.timeclock.usr_id.readable = False
if auth.is_logged_in():
    db.timeclock.usr_id.default = auth.user.id
    
db.define_table('siri_projects',
    Field('name', 'string', label='Name'),
    Field('description', 'text', label='Description'),
    Field('coordinator', 'string', label='Coordinator'),
    Field('contact_org', 'string', label='Organization'),
    Field('contact_name', 'string', required=True, label='Contact Person'),
    Field('contact_phone', 'string', label='Contact Phone'),
    Field('contact_email', 'string', required=True, label='Contact Email'),
    Field('contact_loc', 'string', label='Contact Location'),
    Field('num_students', 'integer', label='# of Students'),
    Field('reviewed', 'boolean', label='Reviewed'),
    Field('contracted', 'boolean', label='Contracted'),
    Field('is_active', 'boolean', label='Active')
)
db.siri_projects.reviewed.default=False

db.define_table('siri_mentors',
    Field('usr_id','reference auth_user'),
    Field('project', 'string'),
    Field('name', 'string'),
    Field('phone', 'string'),
    Field('email', 'string'),
    Field('organization', 'string'),
    Field('org_title', 'string'),
    Field('mentor_type', 'string')
)
db.siri_mentors.project.requires = IS_IN_DB(db,'siri_projects.project_name')
db.siri_mentors.mentor_type.requires = IS_IN_SET(['Full Mentor', 'Student Contact', 'Coordinator','Proect Mentor'])
db.siri_mentors.usr_id.writable = db.siri_mentors.usr_id.readable = False
if auth.is_logged_in():
    db.siri_mentors.usr_id.default=auth.user.id

db.define_table('siri_students',
    Field('usr_id','reference auth_user'),
)
db.siri_students.usr_id.writable = db.siri_students.usr_id.readable = False
if auth.is_logged_in():
    db.siri_students.usr_id.default=auth.user.id

# for the dashboard bulletin board
db.define_table('bulletin_post',
    Field('body', 'string',label="Your comment"),
    auth.signature)

db.define_table('fs_volunteers',
    Field('usr_id','reference auth_user'),
    Field('opp_location','string',required=True),
    Field('internship','boolean'),
    Field('confirmed','boolean'),
    Field('paid','boolean'),
    Field('airfare_purchased','boolean'),
    Field('housing_conf','boolean'),
    Field('training_hotel','boolean'),
    Field('training_hotel_resrv','boolean'),
    Field('training_start','date'),
    Field('training_end','date'),
    Field('depart_date','date'),
    Field('return_date','date'),
    Field('work_start','date'),
    Field('work_end','date'),
    Field('birthday','date'),
    Field('emergency_name','string'),
    Field('emergency_phone','string'),
    Field('archive','boolean')
)
db.fs_volunteers.opp_location.requires = IS_IN_SET(['Madrid', 'Dominican Republic', 'Montreal'])

db.define_table('fs_prospects',
    Field('usr_id','reference auth_user'),
    Field('candidate','boolean'),
    Field('interested_location','string'),
    Field('interested_dates','string'),
    Field('speak_language','string'),
    Field('language_level','integer'),
    Field('referred_by','string'),  #**** how do I make it an option list
    Field('resume','upload')
)
db.fs_prospects.interested_location.requires = IS_IN_SET(['Madrid', 'Dominican Republic', 'Montreal','New Hampshire'])
db.fs_prospects.speak_language.requires = IS_IN_SET(['Spanish', 'French', 'Other'])
db.fs_prospects.language_level.requires = IS_IN_SET(['1 - Beginner', '2 - I know a few phrases', '3 - I can get by on my own', '4 - I am conversational', '5 - Native/Fluent'])
db.fs_prospects.referred_by.requires = IS_IN_SET(['International Studies Instructor', 'Language Instructor', 'University Email', 'Know someone who went to a meeting', 'Know someone who participated', 'Found the website'])

## after defining tables, uncomment below to enable auditing
auth.enable_record_versioning(db)

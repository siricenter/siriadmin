@auth.requires_login()	
def employeedash():
    """
    this will become the index page
    """
    fields = ['project','work_date','time_in','time_out','description']
    form = SQLFORM(db.timeclock, submit_button='Submit Hours', fields=fields)
    if form.process(onvalidation=calcHours).accepted:
        response.flash = 'Thank you for submitting your time ' + str(form.vars.hours)
    elif form.errors:
        response.flash = 'There was an error on the form'
    else:
        response.flash = 'Welcome to your dashboard ' + session.auth.user.first_name
    response.title = session.auth.user.first_name + "'s Dashboard"
    response.subtitle = 'Add or review time clock submissions'

    query = db.timeclock.usr_id == session.auth.user.id
    clockEntries = db(query).select(db.timeclock.ALL, orderby=~db.timeclock.work_date)
    totalHours = 0
    # TODO: this is totaling all hours not just the displayed hours
    # for entry in clockEntries:
    #     totalHours += float(entry.hours)
    return dict(form=form, clockEntries=clockEntries, totalHours=totalHours)

@auth.requires_login()
def addtime():
    """
    Allows a loggedin user to add an entry for time worked
    """
    form = SQLFORM(db.timeclock)
    if form.process().accepted:
        response.flash = 'Thank you for submitting your time'
    elif form.errors:
        response.flash = 'There was an error on the form'
    else:
        response.flash = 'Welcome ' + session.auth.user.first_name + ' your id is: ' + str(session.auth.user.id)
    response.title = 'New Entry'
    response.subtitle = 'please fill out the form below'
    hoursTest = type(db.timeclock.time_in)
    return dict(form=form, hoursTest=hoursTest)

@auth.requires_login()
def displaytime():
    """
    Shows the entries for the user that is logged in
    TODO: add a 'request change' link for employees to request a change to an entry
    """
    payPeriods = 0	
    query = db.timeclock.usr_id == session.auth.user.id
    grid = SQLFORM.grid(query, deletable=False, editable=False, create=False, orderby=~db.timeclock.work_date)

    return dict(grid=grid)

@auth.requires_login()
def processinvoices():
    """
    A view to process and export invoices or various clients
    TODO: make it variable per client and per period via inputs of some type
          have it call the gspread function
          process a log of some sort
          display a processing icon and confirmation message
    """
    form=FORM('Invoice Details:',
              INPUT(_start='start', requires=IS_NOT_EMPTY()),
              INPUT(_end='end', requires=IS_NOT_EMPTY()),
              INPUT(_project='project', requires=IS_NOT_EMPTY()),
              INPUT(_type='submit'))
    if form.accepts(request,session):
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'

    return dict(form=form)

def calcHours(form):
    # TODO: make this ok for non 24 hour time
    hourDiff = int(form.vars.time_out[0:2]) - int(form.vars.time_in[0:2])
    minDiff = (int(form.vars.time_out[3:5]) - int(form.vars.time_in[3:5]))/60.0
    form.vars.hours = hourDiff + minDiff

def gdatatest():
    """
    testing integration with Google
    """

    gemail = 'dawg3tt@gmail.com'
    gpwd = 'mol090901!'

    # ############ get docs list example #################################################
    # # Create a client class which will make HTTP requests with Google Docs server.
    # gdocsClient = gdata.docs.service.DocsService()
    # # Authenticate using your Google Docs email address and password.
    # gdocsClient.email = gemail
    # gdocsClient.password = gpwd
    # gdocsClient.source = 'SIRI Admin'
    # gdocsClient.ProgrammaticLogin()
    # # Query the server for an Atom feed containing a list of your documents.
    # docsFeed = gdocsClient.GetDocumentListFeed()
    # ####################################################################################
    
    # return dict(docsFeed=docsFeed)

def gspreadtest():
    clockEntries = db(db.timeclock.project == 'DDM').select(db.timeclock.ALL, orderby=~db.timeclock.usr_id)

    gc = gspread.login('dawg3tt@gmail.com', 'mol090901!')
    ss = gc.open("web2py_tester")
    wks = ss.sheet1
    timeList = wks.range('A16:E30')
    for cell in timeList:
        cell.value = ''
    # wks.update_cells(timeList)
    newks = ss.add_worksheet(title='clockEntries[0].usr_id', rows="30", cols="6")
    newks.update_cell(1,1, 'Invoice')
    copyRange = wks.range('A1:F30')
    newRange = newks.range('A1:F30')
    # for cell in newRange:
    #     cell.value = copyRange.value
    copyList = wks.get_all_values()
    newks.update_cells(copyRange)

    update = False
    if update:
        rate = 10
        idx = 16
        for entry in clockEntries:
            wks.update_cell(idx, 1, entry.work_date)
            wks.update_cell(idx, 2, entry.description)
            wks.update_cell(idx, 3, entry.hours)
            wks.update_cell(idx, 4, rate) #TODO: this should be replaced by a query for rate added by admin
            wks.update_cell(idx, 5, rate*entry.hours)
            idx += 1

    return dict(
        timeList=timeList, 
        clockEntries=clockEntries, 
        wks=wks,
        newks=newks,
        copyRange=copyRange, 
        copyList=copyList
        )

# def copyCells(values, newks):
#     for row in values:
#         for cell in rows:

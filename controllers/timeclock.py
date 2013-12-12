########## Some Global Variables ##############
"""
We need to find the current pay period
"""
FIRST_PERIOD_START = datetime(2013, 11, 10) # TODO: Get this set to the beginning of a pay period ############################
PERIOD_START = FIRST_PERIOD_START           # TODO: implement tzinfo to make datetimes aware ############################
PAY_PERIOD = timedelta(weeks = 2) - timedelta(microseconds=1)
PERIOD_END = PERIOD_START + PAY_PERIOD
NOW = datetime.now()
while not (PERIOD_START <= NOW < PERIOD_END):
    PERIOD_START += timedelta(weeks = 2)
    PERIOD_END = PERIOD_START + PAY_PERIOD

def index():
    redirect(URL(employeedash))

@auth.requires_login()
def employeedash():
    """
    this will become the index page
    TODO: create a clockin clockout feature ######################################################################
    """
    fields = ['project','work_date','time_in','time_in_ampm','time_out','time_out_ampm','description']
    form = SQLFORM(db.timeclock, submit_button='Submit Hours', fields=fields)
    if form.process(onvalidation=calcHours).accepted:
        response.flash = 'Thank you for submitting your time ' + str(form.vars.hours)
    elif form.errors:
        response.flash = 'There was an error on the form'
    else:
        response.flash = 'Welcome to your dashboard ' + session.auth.user.first_name
    response.title = session.auth.user.first_name + "'s Dashboard"
    response.subtitle = 'Current pay period is ' + PERIOD_START.strftime("%m/%d/%Y") + ' - ' + PERIOD_END.strftime("%m/%d/%Y")

    query = (db.timeclock.usr_id == session.auth.user.id)&(db.timeclock.work_date > PERIOD_START)&(db.timeclock.work_date < PERIOD_END)
    clockEntries = db(query).select(db.timeclock.ALL, orderby=~db.timeclock.work_date)
    sum = db.timeclock.hours.sum()
    totalHours = db(query).select(sum).first()[sum] or 0

    return locals() #dict(form=form, clockEntries=clockEntries, totalHours=totalHours)

@auth.requires_signature()
def ask():
    form=SQLFORM.factory(
        Field('message', 'text', requires=IS_NOT_EMPTY()))
    if form.process().accepted:
        if mail.send(to='e.caldwell@sirinstitute.org',
                  subject='from %s' % session.auth.user.email,
                  message = form.vars.question):
            response.flash = 'Thank you'
            response.js = "jQuery('#%s').hide()" % request.cid
        else:
            form.errors.your_email = "Unable to send the email"
    return form

@auth.requires_login()
def addtime():
    """
    Allows a logged in user to add an entry for time worked
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
    TODO: fix the modal comment/question submit error  ################################
    """
    payPeriods = 0	
    query = db.timeclock.usr_id == session.auth.user.id
    grid = SQLFORM.grid(query, deletable=False, editable=False, create=False, orderby=~db.timeclock.work_date)

    return dict(grid=grid)

@auth.requires_login()
def bulletin_board():
    """
    Shows the bulletin board and the form to submit a new comment
    Includes pagination.
    """
    if len(request.args):
        page=int(request.args[0])
    else:
        page = 0
    items_per_page=5
    limitby=(page * items_per_page, (page + 1) * items_per_page + 1)
    comments=db(db.bulletin_post).select(limitby=limitby, orderby=~db.bulletin_post.created_on)

    form=SQLFORM(db.bulletin_post).process(next=URL(args=[0]))
    return locals()

@auth.requires_login()
def processinvoices():
    """
    A view to process and export invoices or various clients
    TODO: make it variable per client and per period via inputs of some type #########################################
          have it call the gspread function
          process a log of some sort
          display a processing icon and confirmation message
    """
    
    form=FORM('Invoice Details:',
              INPUT(_name='start', _class='date', requires=IS_NOT_EMPTY()),
              INPUT(_name='end', _class='date', requires=IS_NOT_EMPTY()),
              INPUT(_name='project', requires=IS_NOT_EMPTY()),
              INPUT(_type='submit'))

    if form.accepts(request,session):
        response.flash = 'form accepted'
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill out the form'
    # Get the vars from the form to process the invoices
    start = form.vars.start
    end = form.vars.end
    project = form.vars.project
    # Initialize various variables to use in the function
    clockSet = None
    empIdList = []
    empInfo = []
    empList = []
    totalHours = 0
    # Initialize a Google Docs client
    gc = gspread.login('dawg3tt@gmail.com', 'mol090901!')
    # Check to see if the form has been submitted
    # TODO: tie this to the form submission, maybe using onvalidation ###################################################
    if start is not None:
        response.flash = "Processing Invoices for " + project + ", period: " + start + " - " + end
        # Convert form variables to date objects
        start = datetime.strptime(start, "%m/%d/%Y")
        end = datetime.strptime(end, "%m/%d/%Y")
        # Query and select records from the database that match the form variables
        query = (db.timeclock.work_date >= start) & (db.timeclock.work_date <= end) & (db.timeclock.project == project)
        clockEntries = db(query).select(db.timeclock.ALL, orderby=~db.timeclock.work_date)
        # Get a list of unique employee ids from the time submissions
        for item in clockEntries:
            empIdList.append(item.usr_id)
        empIdList = set(empIdList)
        # Build a list of Employee object instances
        for id in empIdList:
            empInfo = db(db.auth_user.id == id).select().first()
            # Instantiate an Employee object, initialize an empty array for timeclock entries and a variable to hold the total hours
            emp = Employee(id, empInfo.first_name, empInfo.last_name, empInfo.email)
            emp.entries = []
            emp.totalHours = 0
            emp.project = project
            # Add the timeclock entries for this employee to the empty array and calculate the total hours
            for entry in clockEntries:
                if entry.usr_id == id:
                    emp.entries.append(entry)
                    emp.totalHours += entry.hours
            # Add the new Employee object to the Employee object list
            empList.append(emp)

        # For each id create an invoice and format it
        for employee in empList:
            # call functions to create and format invoices
            # TODO: find a way to create new invoices programmatically ##################################################
            createInvoices(employee, gc, start, end)
            # formatIncoices()
    
        clockEntries = []
        entryRange = []


    return dict(form=form, clockEntries=clockEntries, empList=empList, empInfo=empInfo)

def createInvoices(employee, gc, start, end):
    """
    A function to create a Google doc with an invoice or each employee
    """
    response.flash = "Creating Invoices"
    ss = gc.open("web2py_tester")
    wks = ss.sheet1
    newks = ss.add_worksheet(title=employee.firstName + " " + employee.lastName, rows="70", cols="5")
    headerRange = newks.range('A1:E15')
    entryRange = newks.range('A16:E' + str(len(employee.entries) + 15))
    for cell in headerRange:
        cell.value = ''
    headerRange[0].value = "Invoice"
    headerRange[10].value = "From:"
    headerRange[11].value = employee.firstName + " " + employee.lastName
    headerRange[13].value = "Period"
    headerRange[18].value = "From:"
    headerRange[19].value = "To:"
    headerRange[23].value = start
    headerRange[24].value = end
    headerRange[40].value = "To:"
    headerRange[41].value = "Deseret Digital Media"
    headerRange[44].value = "Hours Total"
    headerRange[46].value = "55 North 300 West Ste 500"
    headerRange[49].value = employee.totalHours
    headerRange[51].value = "Salt Lake City, UT 84101"
    headerRange[54].value = "Total"
    headerRange[56].value = "801-333-7400"
    headerRange[59].value = employee.totalHours * 10
    headerRange[70].value = "Date"
    headerRange[71].value = "Description"
    headerRange[72].value = "Hours"
    headerRange[73].value = "Rate"
    headerRange[74].value = "Subtotal"

    outputEntries = convertGdOutput(employee.entries)
    i = 0
    for cell in entryRange:
        cell.value = outputEntries[i]
        i += 1

    newks.update_cells(headerRange)
    newks.update_cells(entryRange)

def convertGdOutput(entries):
    # convert a set of time entries from the database to a valid Google Docs format
    outputEntries = []
    for entry in entries:
        outputEntries.extend([entry.work_date, entry.description, entry.hours, 10, float(entry.hours) * 10])
    return outputEntries


def calcHours(form):
    timeIn = form.vars.time_in
    timeOut = form.vars.time_out
    timeInAmPm = form.vars.time_in_ampm
    timeOutAmPm = form.vars.time_out_ampm
    timeInHour = int(timeIn[0:2])
    timeInMin = int(timeIn[3:5])
    timeOutHour = int(timeOut[0:2])
    timeOutMin = int(timeOut[3:5])
    if timeInAmPm == 'PM':
        timeInHour += 12
    if timeOutAmPm == 'PM':
        timeOutHour += 12
    hourDiff = timeOutHour - timeInHour
    minDiff = (timeOutMin - timeInMin)/60.0
    form.vars.hours = "%.2f" % (hourDiff + minDiff)

def gdatatest():
    """
    testing integration with Google
    """
    gemail = 'dawg3tt@gmail.com'
    gpwd = 'mol090901!'

    ############ get docs list example #################################################
    # Create a client class which will make HTTP requests with Google Docs server.
    gdataClient = gdata.docs.service.DocsService()
    # Authenticate using your Google Docs email address and password.
    gdataClient.email = gemail
    gdataClient.password = gpwd
    gdataClient.source = 'SIRI Admin'
    gdataClient.ProgrammaticLogin()
    # Query the server for an Atom feed containing a list of your documents.
    docsFeed = gdataClient.GetDocumentListFeed()
    ####################################################################################
    
    return dict(docsFeed=docsFeed)

def gspreadtest():
    clockEntries = db(db.timeclock.project == 'DDM').select(db.timeclock.ALL, orderby=~db.timeclock.usr_id)

    gc = gspread.login('dawg3tt@gmail.com', 'mol090901!')
    ss = gc.open("web2py_tester")
    wks = ss.sheet1
    timeList = wks.range('A16:E30')
    for cell in timeList:
        cell.value = ''
    # wks.update_cells(timeList)
    newks = ss.add_worksheet(title='clockEntries[0].usr_id', rows="70", cols="5")
    newks.update_cell(1,1, 'Invoice')
    copyRange = wks.range('A1:F30')
    headerRange = newks.range('A1:F30')
    # for cell in headerRange:
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
            wks.update_cell(idx, 4, rate) #TODO: this should be replaced by a query for rate added by admin ################
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

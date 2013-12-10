################################################################
#          this is a model for user defined classes            #
################################################################

class Employee(object):
	""" A class for Employees """
	def __init__(self, id, firstName, lastName, email):
		self.firstName=firstName
		self.lastName=lastName
		self.email=email
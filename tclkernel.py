from ipykernel.kernelbase import Kernel
from io import StringIO
import traceback
import tkinter
import sys
import os
import os.path

def read_file(filename):
	data = ""
	if os.path.isfile(filename):
		with open(filename, 'r') as file:
			data = file.read()
	return data

def remove_file(filename):
	if os.path.isfile(filename):
		os.remove(filename)

# Simple function to find all placements of a character in a string
def findall(str, c):
	l = []
	for i, ltr in enumerate(str):
		if ltr == c:
			l.append(i)
	return l

# Define a subclass of Kernel that handles some pre-defined functions
class TclKernel(Kernel):
	# Display banner for the Kernel
	banner = "Tcl Kernel"

	# Define Implementation specifics
	implementation = 'Tcl Kernel'
	implementation_version = '1.0'

	# Define some language metadata. name will define the syntax highlighting
	language_info = {
		'version': '0.1',
		'name': 'tcl',
		'mimetype': 'text/plain',
		'file_extension': '.tcl',
	}

	# Create a Tcl interpreter at an instance level so previous commands output is still in scope
	interp = tkinter.Tcl()

	# Evaluate a tcl file to redefine some procs for usage on the web
	interp.evalfile('tcl_kernel.tcl')

	# Check to see if the code has completed. A quick and dirty implementation to check {}
	def do_is_complete(self, code):
		# Get the number of unmatched brackets for a simple check of code completion
		# TODO
		diff = len(findall(code, '{')) - len(findall(code, '}'))
		# return dict with status of complete if it is complete. This will allow for code to be executed
		# return dict with status of incomplete if otherwise. This will prompt the user with the indent on the following line
		# (the indent will be read when the code is executed so pick a string that can be executed (like " " or "\t"))
		return {
			'status': 'complete' if diff==0 else 'incomplete',
			'indent': ""
		}

	# Execute the TCL code 
	def do_execute(self, code, silent, store_history=True, user_expressions=None, allow_stdin=False):
		if not silent:
			# Default string in case something errors
			response = "Error: something happened"
			remove_file("temp.temp")
			
			# Catch any errors in user code
			try:
				# Execute user code and read a returned string into response
				response = self.interp.tk.eval(code)

				fileout = read_file("temp.temp")
				response = fileout + response
				
				# use the response variable and tell Jupyter that the output is stdout (normal text)
				stream_content = {'name': 'stdout', 'text': response}
			except Exception as err:
				# Catch any errors and pass the text back as stderr (red error text)
				stream_content = {'name': 'stderr', 'text': str(err)}

			# publish the text back to the user
			self.send_response(self.iopub_socket, 'stream', stream_content)

		# Return status text as dictionary
		return {	
				'status': 'ok',
				# The base class increments the execution count
				'execution_count': self.execution_count,
				'payload': [],
				'user_expressions': {},
			}

# In case this module is run directly from the command line
if __name__ == '__main__':
	from ipykernel.kernelapp import IPKernelApp
	IPKernelApp.launch_instance(kernel_class=TclKernel)

from contextlib import contextmanager
from ipykernel.kernelbase import Kernel
import ctypes
import re
import io
import os
import os.path
import platform
import sys
import tempfile
import tkinter
import traceback

def read_file(filename):
	data = ""
	if os.path.isfile(filename):
		with open(filename, 'r') as file:
			data = file.read()
	return data

def remove_file(filename):
	if os.path.isfile(filename):
		os.remove(filename)

# Below code taken from https://github.com/rpep/tcl_kernel/blob/master/tcl_kernel/kernel.py
OS = platform.platform()
libc = ctypes.CDLL(None)
if 'Darwin' in OS:
	c_stdout = ctypes.c_void_p.in_dll(libc, '__stdoutp')
elif 'Linux' in OS:
	c_stdout = ctypes.c_void_p.in_dll(libc, 'stdout')
else:
	print("""Your OS is not currently compatible with this Kernel \n
	     Please make an issue here: \n
	     https://github.com/ryanpepper/tcl_kernel
	     """)

@contextmanager
def stdout_redirector(stream):
	# The original fd stdout points to. Usually 1 on POSIX systems.
	original_stdout_fd = sys.__stdout__.fileno()

	def _redirect_stdout(to_fd):
		"""Redirect stdout to the given file descriptor."""
		# Flush the C-level buffer stdout
		libc.fflush(c_stdout)

		# Flush and close sys.stdout - also closes the file descriptor (fd)
		sys.stdout.close()

		# Make original_stdout_fd point to the same file as to_fd
		os.dup2(to_fd, original_stdout_fd)

		# Create a new sys.stdout that points to the redirected fd
		sys.stdout = io.TextIOWrapper(os.fdopen(original_stdout_fd, 'wb'))

	# Save a copy of the original stdout fd in saved_stdout_fd
	saved_stdout_fd = os.dup(original_stdout_fd)
	try:
		# Create a temporary file and redirect stdout to it
		tfile = tempfile.TemporaryFile(mode='w+b')
		_redirect_stdout(tfile.fileno())

		# Yield to caller, then redirect stdout back to the saved fd
		yield
		_redirect_stdout(saved_stdout_fd)

		# Copy contents of temporary file to the given stream
		tfile.flush()
		tfile.seek(0, io.SEEK_SET)
		stream.write(tfile.read())
	finally:
		tfile.close()
		os.close(saved_stdout_fd)

# End copied code

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
	interp.evalfile('kernel_tcl.tcl')

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
			new_stdout = io.BytesIO()
			stream_content = {}
			
			# Catch any errors in user code
			with stdout_redirector(new_stdout):
				try:
					# Execute user code and read a returned string into response
					response = self.interp.tk.eval(code)

					# use the response variable and tell Jupyter that the output is stdout (normal text)
					stream_content = {'name': 'stdout', 'text': response}
				except Exception as err:
					# Catch any errors and pass the text back as stderr (red error text)
					stream_content = {'name': 'stderr', 'text': str(err)}


			
			text = new_stdout.getvalue().decode('utf-8')
			text = re.sub(r"\\r\\n", "\n", text)
			stream_content['text'] = str(text) + str(stream_content['text'])
			# publish the text back to the user
			self.send_response(self.iopub_socket, 'stream', stream_content)

			output = new_stdout.getvalue()
			response = str(output) + response

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

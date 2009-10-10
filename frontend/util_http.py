class http_response(object):
	def __init__(self, environ, start_response):
		import cStringIO
		self.buffer = cStringIO.StringIO()
		self.environ = environ
		self.start_response = start_response
		self.status = '200 OK'
		self.headers = [('Content-type', 'text/html; charset=utf-8'), ('P3P', '''policyref="/w3c/p3p.xml", CP="NOI NOR CURa OUR"''')]

	def write(self, data):
		self.buffer.write(data)

	def finalise(self):
		"""
		Closes the output buffer, writes the correct header/s and returns
		something suitable for returning from the top-level application() call
		"""
		self.value = self.buffer.getvalue()
		self.buffer.close()
		self.headers.append(('Content-Length', str(len(self.value))))
		self.start_response(self.status, self.headers)
		return [self.value]

	def redirect(self, url):
		self.buffer.close()
		self.status = '302 Found'
		self.headers = [('Content-Type', 'text/html'), ('Location', url)]
		self.start_response(self.status, self.headers)
		return ['redirecting']

	def user_failure(self, msg):
		self.status = '400 User error'
		print >>self.buffer, "HTTP 400 - error in request<br />"
		print >>self.buffer, str(msg)
		return self.finalise()

	def not_found(self, msg):
		self.status = '404 Not found'
		print >>self.buffer, "HTTP 404 - not found<br />"
		print >>self.buffer, str(msg)
		return self.finalise()


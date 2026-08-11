import bf2
import host
import mm_utils
import socket

__version__ = 1.0

__required_modules__ = {
	'modmanager': 1.6
}


__supports_reload__ = True


__supported_games__ = {
	'bf2': True,
	'bf2142': True
}


__description__ = "KokubanModule v%s" % __version__


configDefaults = {
	'address': "127.0.0.1",
	'port': 80,
	'token': "",
}

class KokubanModule( object ):

	def __init__( self, modManager ):
		self.mm = modManager
		self.mm.SendAdminEvent = self.SendAdminEvent
		self.__state = 0

	def init( self ):
		self.__config = self.mm.getModuleConfig( configDefaults )

		if 0 == self.__state: pass

		self.__state = 1

	## type: int, recipient: str, param: int, text: str
	def SendAdminEvent(self, type, recipient, param, text = ""):
		"""
		type:	ban = 0
				kick = 1
				other = 2

		param: 	profile = 0
				key hash = 1
				broadcast = 2

		recipient:
				param == profile: player nickname
				param == key hash: key hash (string of 32 characters)
				param == broadcast: None

		text: custom additional text that the player will see with the notification
		"""

		response = self._http_get(self.__config['address'], self.__config['port'], "/api/sendadminevent?type=%s&param=%s&text=%s&recipient=%s" % (type, param, text, recipient), {'auth': self.__config['token']})
		self.mm.info("%s %s %s" % (response["status"], response["headers"], response["body"]))


	def _http_request(self, host, port, method, path, headers=None, body=None, timeout=10):
		if headers is None:
			headers = {}

		if body is None:
			body = ""

		request = method + " " + path.replace(" ", "%20") + " HTTP/1.0\r\n"
		request += "Host: " + host + "\r\n"

		if body:
			request += "Content-Length: " + str(len(body)) + "\r\n"

		for name in headers:
			request += name + ": " + headers[name] + "\r\n"

		request += "\r\n"
		request += body

		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(timeout)

		try:
			sock.connect((host, port))

			data = request
			while data:
				sent = sock.send(data)
				if sent <= 0:
					raise IOError("Socket connection broken")
				data = data[sent:]

			response = ""
			while True:
				data = sock.recv(4096)

				if not data:
					break

				response += data

		finally:
			sock.close()

		return self._parse_http_response(response)


	def _parse_http_response(self, response):
		separator = "\r\n\r\n"
		pos = response.find(separator)

		if pos == -1:
			raise IOError("Invalid HTTP response")

		header_data = response[:pos]
		body = response[pos + len(separator):]

		lines = header_data.split("\r\n")

		status_line = lines[0]
		parts = status_line.split(" ", 2)

		if len(parts) < 2:
			raise IOError("Invalid HTTP status line")

		version = parts[0]
		status = int(parts[1])

		if len(parts) >= 3:
			reason = parts[2]
		else:
			reason = ""

		headers = {}

		for line in lines[1:]:
			colon = line.find(":")

			if colon == -1:
				continue

			name = line[:colon].strip().lower()
			value = line[colon + 1:].strip()

			headers[name] = value

		return {
			"version": version,
			"status": status,
			"reason": reason,
			"headers": headers,
			"body": body
		}


	def _http_get(self, host, port=80, path="/", headers=None, timeout=10):
		return self._http_request(
			host,
			port,
			"GET",
			path,
			headers,
			None,
			timeout
		)

	def _http_post(host, port=80, path="/", body="", headers=None, timeout=10):
		if headers is None:
			headers = {}

		if "Content-Type" not in headers:
			headers["Content-Type"] = "application/x-www-form-urlencoded"

		return self._http_request(
			host,
			port,
			"POST",
			path,
			headers,
			body,
			timeout
		)

	def shutdown( self ):
		self.__state = 2
		self.mm.SendAdminEvent = None

	def update( self ):
		pass

def mm_load( modManager ):
	return KokubanModule( modManager )

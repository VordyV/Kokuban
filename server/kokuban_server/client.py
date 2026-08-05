from tornado.iostream import IOStream
import uuid
import time


class Client:

	def __init__(self, address: str, port: int, stream: IOStream, server):
		self.__id = uuid.uuid4().hex
		self.__address: str = address
		self.__stream: IOStream = stream
		self.__server = server
		self.__port: int = port
		self.__profile: str | None = None
		self.__game_server: str | None = None
		self.__auth_data: str | None = None
		self.__key_hash: str | None = None
		self.__lpt: int = int(time.time()) # last ping time
		self.__lsprt: int = int(time.time()) # last successful ping response time

	@property
	def id(self): return self.__id

	@property
	def address(self) -> str: return self.__address

	@property
	def stream(self) -> IOStream: return self.__stream

	@property
	def server(self): return self.__server

	@property
	def port(self) -> int: return self.__port

	@property
	def profile(self) -> str | None: return self.__profile

	@property
	def game_server(self) -> str | None: return self.__profile

	@property
	def auth_data(self) -> str | None: return self.__auth_data

	@property
	def LPT(self) -> int | None: return self.__lpt

	@property
	def LSPRT(self) -> int | None: return self.__lsprt

	@property
	def key_hash(self) -> str | None: return self.__key_hash

	def set_profile(self, value: str | None): self.__profile = value
	def set_game_server(self, value: str | None): self.__game_server = value
	def set_auth_data(self, value: str): self.__auth_data = value
	def set_LPT(self, value: int): self.__lpt = value
	def set_LSPRT(self, value: int): self.__lsprt = value
	def set_key_hash(self, value: str): self.__key_hash = value

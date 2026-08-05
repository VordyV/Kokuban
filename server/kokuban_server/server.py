from tornado.tcpserver import TCPServer
from tornado.iostream import StreamClosedError, IOStream
from .client import Client
from .package_type import PackageType
from .package import Package
from .protocol import Protocol
from .error_type import ErrorType
from loguru import logger
import msgspec
import sys
import asyncio
import time


class Server(TCPServer):

	end_packet: bytes = b"\n"

	def __init__(self, core, ping_timeout: int, *args, **kwargs):
		self.__core = core
		self.__ping_timeout = ping_timeout
		self.__clients = set()
		super().__init__(*args, **kwargs)

	@property
	def core(self): return self.__core

	@property
	def clients(self) -> set: return self.__clients

	async def handle_stream(self, stream, address):
		client = Client(address=address[0], port=address[1], stream=stream, server=self)
		logger.info(f"{client.address}:{client.port} connected")
		self.__clients.add(client)

		pkg = None
		pkgs = None
		while True:
			try:
				data = await stream.read_until(Server.end_packet)
				logger.debug(f"{client.address}:{client.port} >> {data} ({len(data)}b)")
				data = data.strip(b"\n")

				pkg = Package.validate_package(data)

				if not pkg:
					logger.debug(f"{client.address}:{client.port} client sent an invalid packet")
					await self._send(Package.create_pkg_error(ErrorType.incorrect_packet_format).get_bytes(), stream, client)
					continue

				pkgs = Protocol.find(pkg.header)
				if pkgs:
					async for p in pkgs(client, pkg):
						logger.debug(f"{client.address}:{client.port} packet sent to client {p.type} {p.body}")
						await self._send(p.get_bytes(), stream, client)
				else:
					await self._send(Package.create_pkg_error(ErrorType.request_header_invalid).get_bytes(), stream, client)
			except StreamClosedError:
				break

		logger.info(f"{client.address}:{client.port} disconnected")
		self.__clients.remove(client)

	async def _send(self, data: bytes, stream: IOStream, client: Client):
		await stream.write(data)
		logger.debug(f"{client.address}:{client.port} << {data} ({len(data)}b)")

	async def ping_all(self):
		tasks = []
		pkg = Protocol.pkg_ping().get_bytes()
		lpt = int(time.time())
		for client in self.__clients.copy():
			if client.stream.closed(): continue
			if client.LPT - client.LSPRT > self.__ping_timeout:
				logger.info(f"{client.address}:{client.port} client is not responding to ping requests and has been disconnected")
				client.stream.close()
				continue

			client.set_LPT(lpt)
			tasks.append(self._send(pkg, client.stream, client))
		await asyncio.gather(*tasks)

	async def broadcast(self, data: bytes):
		tasks = []
		for client in self.__clients.copy():
			if client.stream.closed(): continue
			tasks.append(self._send(data, client.stream, client))
		await asyncio.gather(*tasks)

	def has_key_hash(self, key_hash: str):
		for client in self.__clients.copy():
			if client.key_hash == key_hash: return True
		return False
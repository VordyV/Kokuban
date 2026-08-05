from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession
from loguru import logger
from callixir import AsyncSimpleShell
from fastapi import FastAPI
from .views import router
from rich.live import Live
from rich.table import Table
from rich.console import Console
from .server import Server
from prompt_toolkit import Application
from .protocol import Protocol
import tornado.ioloop
import asyncio
import uvicorn
import time
import random
import datetime


class KokubanServer:

	def __init__(self, address_http: str = "127.0.0.1", port_http: int = 80, address_tcp: str = "127.0.0.1", port_tcp: int = 8080, ping_interval: datetime.timedelta  = datetime.timedelta(seconds=10), ping_timeout: int = 15):
		self.__address_http = address_http
		self.__port_http = port_http
		self.__address_tcp = address_tcp
		self.__port_tcp = port_tcp
		self.__ping_interval = ping_interval
		self.__ping_timeout = ping_timeout
		self.__event_stop = asyncio.Event()
		self.__shell = AsyncSimpleShell()
		self.__fa_app = FastAPI()
		self.__http_server = uvicorn.Server(uvicorn.Config(self.__fa_app, port=self.__port_http, host=self.__address_http, log_level="error"))
		self.__tcp_server = Server(self, self.__ping_timeout)
		self.__task_ping = tornado.ioloop.PeriodicCallback(self.__tcp_server.ping_all, self.__ping_interval)

		self.__fa_app.include_router(router)

		self.__shell.register("notify", self._on_cmd_notify)
		self.__shell.register("showdialog", self._on_cmd_show_dialog)

	async def _on_cmd_notify(self, text: str):
		await self.__tcp_server.broadcast(Protocol.pkg_notify(text).get_bytes())

	async def _on_cmd_show_dialog(self, type: int, *text: str):
		await self.__tcp_server.broadcast(Protocol.pkg_show_dialog(type, " ".join(text)).get_bytes())

	async def _inter_shell(self):
		session = PromptSession("")
		string = ""
		command = None
		while True:
			try:
				string = await session.prompt_async()
				if string.strip() == "": continue
				command = await self.__shell.execute(string)
				if command.error: print(command.error, command.err_traceback)
			except (EOFError, KeyboardInterrupt):
				print("ctrl c")
				self.__event_stop.set()
				return

	async def _loop(self):
		with patch_stdout(raw=True):
			logger.info("Start")
			task_shell = asyncio.create_task(self._inter_shell())
			task_http_server = asyncio.create_task(self.__http_server.serve())
			self.__tcp_server.listen(self.__port_tcp, self.__address_tcp)

			self.__task_ping.start()

			await self.__event_stop.wait()

			self.__task_ping.stop()
			self.__http_server.should_exit = True
			await task_http_server
			logger.info("Stop")

	def start(self):
		asyncio.run(self._loop())




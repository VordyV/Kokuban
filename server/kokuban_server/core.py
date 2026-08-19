from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.shortcuts import PromptSession
from loguru import logger
from callixir import AsyncSimpleShell
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from .package import Package
from .views import router
from .server import Server
from .protocol import Protocol
from .models import server_model
from .admin_event_type import AdminEventType
from .recipient_param_type import RecipientParamType
import tornado.ioloop
import asyncio
import uvicorn
import datetime
import aiosqlite
import os
import time
import kokuban_server


class KokubanServer:

	def __init__(self, address_http: str = "127.0.0.1", port_http: int = 80, address_tcp: str = "127.0.0.1", port_tcp: int = 8080, ping_interval: datetime.timedelta  = datetime.timedelta(seconds=10), ping_timeout: int = 15, database_filename: str = "kb.db"):
		self.__address_http = address_http
		self.__port_http = port_http
		self.__address_tcp = address_tcp
		self.__port_tcp = port_tcp
		self.__ping_interval = ping_interval
		self.__ping_timeout = ping_timeout
		self.__database_filename = database_filename
		self.__event_stop = asyncio.Event()
		self.__shell = AsyncSimpleShell()
		self.__fa_app = FastAPI(title="Kokuban Server API", version=kokuban_server.__version__, docs_url=None, redoc_url=None, lifespan=self._fa_lifespan)
		self.__http_server = uvicorn.Server(uvicorn.Config(self.__fa_app, port=self.__port_http, host=self.__address_http, log_level="error"))
		self.__tcp_server = Server(self, self.__ping_timeout)
		self.__task_ping = tornado.ioloop.PeriodicCallback(self.__tcp_server.ping_all, self.__ping_interval)

		self.__fa_app.include_router(router)

		self.__shell.register("dialog.show", self._on_cmd_show_dialog_all)
		self.__shell.register("dialog.show.pfl", self._on_cmd_show_dialog_profile)
		self.__shell.register("dialog.show.kh", self._on_cmd_show_dialog_keyhash)
		self.__shell.register("ct.show", self._on_cmd_show_central_text_all)
		self.__shell.register("ct.show.pfl", self._on_cmd_show_central_text_profile)
		self.__shell.register("ct.show.kh", self._on_cmd_show_central_text_keyhash)
		self.__shell.register("bsb.set", self._on_cmd_set_bsb_all)
		self.__shell.register("bsb.set.pfl", self._on_cmd_set_bsb_profile)
		self.__shell.register("bsb.set.kh", self._on_cmd_set_bsb_keyhash)
		self.__shell.register("srv.add", self._on_cmd_srv_add)
		self.__shell.register("srv.list", self._on_cmd_srv_list)
		self.__shell.register("srv.upd", self._on_cmd_srv_update)
		self.__shell.register("srv.del", self._on_cmd_srv_delete)
		self.__shell.register("c.list", self._on_cmd_client_list)
		self.__shell.register("help", self._on_cmd_help)

	async def _on_cmd_show_dialog_all(self, type: int,  *text: str): await self.show_dialog_all(AdminEventType(type), " ".join(text))
	async def _on_cmd_show_dialog_profile(self, profile: str, type: int,  *text: str): await self.show_dialog_for_profile(profile, AdminEventType(type), " ".join(text))
	async def _on_cmd_show_dialog_keyhash(self, keyhash: str, type: int,  *text: str): await self.show_dialog_for_keyhash(keyhash, AdminEventType(type), " ".join(text))

	async def _on_cmd_show_central_text_all(self, period: int, *text: str): await self.show_central_text_all(period=period, text=" ".join(text))
	async def _on_cmd_show_central_text_profile(self, profile: str, period: int, *text: str): await self.show_central_text_for_profile(profile=profile, period=period, text=" ".join(text))
	async def _on_cmd_show_central_text_keyhash(self, keyhash: str, period: int, *text: str): await self.show_central_text_for_keyhash(keyhash=keyhash, period=period, text=" ".join(text))

	async def _on_cmd_srv_add(self, name: str, comment: str = ""):
		name = name.strip().replace(" ", "_")

		async with aiosqlite.connect(self.__database_filename) as db:
			cursor = await db.execute(f"SELECT * FROM Server WHERE Name = '{name}';")
			if len(await cursor.fetchall()) >= 1: raise Exception(f"A server with that name `{name}` has already been added")

			token = os.urandom(32).hex()
			dt_create = int(time.time())
			await db.execute(f"INSERT INTO Server (Name, Comment, Token, DTCreate, DTUpdate) VALUES ('{name}', '{comment}', '{token}', '{dt_create}', '{dt_create}');")
			await db.commit()

			print(f"New server {name} has been added\nAccess token[confidential]: {token}")

	async def _on_cmd_srv_list(self):
		async with aiosqlite.connect(self.__database_filename) as db:
			cursor = await db.execute(f"SELECT * FROM Server;")
			rows = ""
			async for srv in cursor:
				rows += "{:<5} {:<15} {:<20} {:<10} {:<20} {:<20}\n".format(srv[0], srv[1], "..." if srv[2].strip() == "" else srv[2], srv[3][-5:], datetime.datetime.fromtimestamp(srv[4]).strftime('%d.%m.%Y %H:%M:%S'), datetime.datetime.fromtimestamp(srv[5]).strftime('%d.%m.%Y %H:%M:%S'))

			if rows == "":
				print("Empty.")
			else:
				print("{:<5} {:<15} {:<20} {:<10} {:<20} {:<20}".format("ID", "Name", "Comment", "Token", "Created", "Updated"))
				print(rows)

	async def _on_cmd_srv_update(self, name: str, param: str, value: str):
		name = name.strip().replace(" ", "_")

		async with aiosqlite.connect(self.__database_filename) as db:
			cursor = await db.execute(f"SELECT * FROM Server WHERE Name = '{name}';")
			if not len(await cursor.fetchall()) >= 1: raise Exception(f"Server with name `{name}` not found")

			if param == "name":
				new_name = value.strip().replace(" ", "_")
				await db.execute(f"UPDATE Server SET Name = '{new_name}', DTUpdate = '{int(time.time())}' WHERE Name = '{name}';")
				await db.commit()

				print(f"Server name {name} has been changed to {new_name}")

			elif param == "comment":
				await db.execute(f"UPDATE Server SET Comment = '{value.strip()}', DTUpdate = '{int(time.time())}' WHERE Name = '{name}';")
				await db.commit()

				print(f"Comment has been changed")

			else:
				print(f"Invalid parameter specified. Possible updates: name, comment")

	async def _on_cmd_srv_delete(self, name: str):
		name = name.strip().replace(" ", "_")

		async with aiosqlite.connect(self.__database_filename) as db:
			cursor = await db.execute(f"SELECT * FROM Server WHERE Name = '{name}';")
			if not len(await cursor.fetchall()) >= 1: raise Exception(f"Server with name `{name}` not found")

			await db.execute(f"DELETE FROM Server WHERE Name = '{name}';")
			await db.commit()

			print(f"Server {name} has been deleted")

	async def _on_cmd_client_list(self):
		rows = ""
		num = 0
		cur_time = int(time.time())
		for c in self.__tcp_server.clients.copy():
			num += 1
			rows += "{:<33} {:<12} {:<12} {:<18} {:<6} {:<12} {:<18}\n".format(c.id, c.address, c.port, c.auth_data if c.auth_data else "not auth", f"{cur_time - c.LSPRT}s", c.profile if c.profile else "...", c.key_hash if c.key_hash else "...")

		if rows == "": print("Empty.")
		else:
			print(f"Total: {num}")
			print("{:<33} {:<12} {:<12} {:<18} {:<6} {:<12} {:<18}".format("ID", "Address", "Port", "Auth", "LSPRT", "Profile", "KeyHash"))
			print(rows)

	async def _on_cmd_set_bsb_all(self, *text): await self.set_BSB_all(" ".join(text) if len(text) > 0 else None)
	async def _on_cmd_set_bsb_profile(self, profile: str, *text): await self.set_BSB_for_profile(profile=profile, text=" ".join(text) if len(text) > 0 else None)
	async def _on_cmd_set_bsb_keyhash(self, keyhash: str, *text): await self.set_BSB_for_keyhash(keyhash=keyhash, text=" ".join(text) if len(text) > 0 else None)

	async def _on_cmd_help(self):
		print(self.__shell.beautiful_help)
	#
	# dialog
	async def show_dialog_for_profile(self, profile: str, type: AdminEventType, text: str):
		await self.send_command(recipient_param=RecipientParamType.Profile, recipient=profile, pkg=Protocol.pkg_show_dialog(type=type.value, text=text))

	async def show_dialog_for_keyhash(self, keyhash: str, type: AdminEventType, text: str):
		await self.send_command(recipient_param=RecipientParamType.KeyHash, recipient=keyhash, pkg=Protocol.pkg_show_dialog(type=type.value, text=text))

	async def show_dialog_all(self, type: AdminEventType, text: str):
		await self.send_command(recipient_param=RecipientParamType.Broadcast, recipient=None, pkg=Protocol.pkg_show_dialog(type=type.value, text=text))
	# dialog
	#

	#
	# central text
	async def show_central_text_for_profile(self, profile: str, text: str, period: int = 7):
		await self.send_command(recipient_param=RecipientParamType.Profile, recipient=profile, pkg=Protocol.pkg_show_central_text(text, period))

	async def show_central_text_for_keyhash(self, keyhash: str, text: str, period: int = 7):
		await self.send_command(recipient_param=RecipientParamType.KeyHash, recipient=keyhash, pkg=Protocol.pkg_show_central_text(text, period))

	async def show_central_text_all(self, text: str, period: int = 7):
		await self.send_command(recipient_param=RecipientParamType.Broadcast, recipient=None, pkg=Protocol.pkg_show_central_text(text, period))
	# central text
	#

	#
	# bottom status bar
	async def set_BSB_for_profile(self, profile: str, text: str | None):
		if text: await self.send_command(recipient_param=RecipientParamType.Profile, recipient=profile, pkg=Protocol.pkg_set_bottom_status_bar(text))
		else: await self.send_command(recipient_param=RecipientParamType.Profile, recipient=profile, pkg=Protocol.pkg_clear_bottom_status_bar())

	async def set_BSB_for_keyhash(self, keyhash: str, text: str | None):
		if text: await self.send_command(recipient_param=RecipientParamType.KeyHash, recipient=keyhash, pkg=Protocol.pkg_set_bottom_status_bar(text))
		else: await self.send_command(recipient_param=RecipientParamType.KeyHash, recipient=keyhash, pkg=Protocol.pkg_clear_bottom_status_bar())

	async def set_BSB_all(self, text: str | None):
		if text: await self.send_command(recipient_param=RecipientParamType.Broadcast, recipient=None, pkg=Protocol.pkg_set_bottom_status_bar(text))
		else: await self.send_command(recipient_param=RecipientParamType.Broadcast, recipient=None, pkg=Protocol.pkg_clear_bottom_status_bar())
	# bottom status bar
	#

	async def send_command(self, recipient_param: RecipientParamType, recipient: str | None, pkg: Package):
		if recipient == None and (recipient_param == recipient_param.Profile or recipient_param == recipient_param.KeyHash): raise Exception("Recipient must not be None for parameters by profile and keyhash")

		if recipient_param == recipient_param.Broadcast: await self.__tcp_server.broadcast(pkg.get_bytes())
		elif recipient_param == recipient_param.Profile: await self.__tcp_server.send_to_profile(pkg.get_bytes(), recipient)
		elif recipient_param == recipient_param.KeyHash: await self.__tcp_server.send_to_keyhash(pkg.get_bytes(), recipient)
		else: raise Exception("Invalid parameter type")

	async def create_tables(self):
		async with aiosqlite.connect(self.__database_filename) as db:
			await db.execute(server_model)

	async def check_token(self, token: str) -> str | None: # server name
		async with aiosqlite.connect(self.__database_filename) as db:
			cursor = await db.execute(f"SELECT * FROM Server WHERE Token = '{token}';")
			data = await cursor.fetchall()
			if len(data) < 1: return None
			return data[0][1]

	async def _inter_shell(self):
		session = PromptSession("")
		string = ""
		command = None
		while True:
			try:
				string = await session.prompt_async()
				if string.strip() == "": continue
				command = await self.__shell.execute(string)
				if command.error: print(command.error)
			except (EOFError, KeyboardInterrupt):
				self.__event_stop.set()
				return

	@asynccontextmanager
	async def _fa_lifespan(self, app: FastAPI):
		app.state.core = self
		yield

	async def _loop(self):
		with patch_stdout(raw=True):
			logger.info("Start")
			await self.create_tables()
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




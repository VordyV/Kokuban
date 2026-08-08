from typing import Any, AsyncGenerator, Callable
from .client import Client
from .package import Package
from .package_type import PackageType
from .error_type import ErrorType
from loguru import logger
import time


def is_auth(func):
	async def wrapper(client: Client, pkg: Package):
		if not client.auth_data:
			yield Package.create_pkg_error(ErrorType.no_auth_data)
			return
		async for p in func(client, pkg):
			yield p
	return wrapper

class Protocol:

	@classmethod
	def find(cls, value: str) -> Callable | None:
		return getattr(cls, f"pkg_{value}", None)

	@staticmethod
	async def pkg_auth(client: Client, pkg: Package) -> AsyncGenerator[Package]:
		agent = pkg.body.get("agent")
		kh = pkg.body.get("kh")
		#
		if not client.auth_data and agent and len(kh) == 32:
			client.set_auth_data(agent)
			logger.info(f"{client.address}:{client.port} authenticated. Agent '{agent}'")
			client.set_key_hash(kh)
			return
			yield
		elif client.auth_data:
			logger.info(f"{client.address}:{client.port} attempted to re-authenticate. Agent '{agent}'")
			yield Package.create_pkg_error(ErrorType.re_auth)
		elif not agent:
			logger.info(f"{client.address}:{client.port} attempted to authenticate with incorrect data")
			yield Package.create_pkg_error(ErrorType.incorrect_auth_data)


		if not kh or len(kh) != 32:
			logger.info(f"{client.address}:{client.port} incorrect key hash")
			yield Package.create_pkg_error(ErrorType.incorrect_key_hash)
		#elif client.server.has_key_hash(kh):
		#	logger.info(f"{client.address}:{client.port} incorrect key hash")
		#	yield Package.create_pkg_error(ErrorType.incorrect_key_hash)

	@staticmethod
	@is_auth
	async def pkg_info(client: Client, pkg: Package) -> AsyncGenerator[Package]:
		yield Package.create_pkg(PackageType.Response, "info", {"ver": "1.0"})

	@staticmethod
	def pkg_notify(text: str):
		return Package.create_pkg(PackageType.Request, "notify", {"txt": text})

	@staticmethod
	def pkg_ping():
		return Package.create_pkg(PackageType.Request, "ping", {})

	@staticmethod
	async def pkg_pong(client: Client, pkg: Package) -> AsyncGenerator[Package]:
		client.set_LSPRT(int(time.time()))
		return
		yield

	@staticmethod
	def pkg_display_text(text: str, period: int = 7):
		return Package.create_pkg(PackageType.Request, "displaytext", {"txt": text, "prd": period})

	@staticmethod
	async def pkg_updateprofile(client: Client, pkg: Package) -> AsyncGenerator[Package]:
		profile = pkg.body.get("profile")
		if not profile or type(profile) != str:
			logger.info(f"{client.address}:{client.port} attempted to update the profile with an incorrect value or did not provide the required 'profile' argument at all")
			yield Package.create_pkg_error(ErrorType.incorrect_profile)
		else:
			logger.info(f"{client.address}:{client.port} profile updated: {profile}")
			client.set_profile(profile)

	@staticmethod
	def pkg_show_dialog(type: int, text: str):
		return Package.create_pkg(PackageType.Request, "showdialog", {"type": type, "txt": text})
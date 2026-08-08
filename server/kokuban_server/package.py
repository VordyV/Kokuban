from __future__ import annotations
from .package_type import PackageType
from .error_type import ErrorType
import msgspec


class Package(msgspec.Struct, array_like=False):
	type: PackageType
	header: str | None
	body: dict[str, object | None]

	def get_bytes(self) -> bytes:
		return msgspec.json.encode(self) + b"\n"

	@staticmethod
	def validate_package(data: bytes) -> Package | None:
		try:
			pkg = msgspec.json.decode(data, type=Package)
			return pkg
		except Exception as e:
			return None

	@staticmethod
	def create_pkg_error(error: ErrorType) -> Package:
		return Package(type=PackageType.Error, header=None, body={"type": error.value})

	@staticmethod
	def create_pkg(type: PackageType, header: str, data: dict[str, object]) -> Package:
		return Package(type=type, header=header, body=data)
from enum import Enum

class PackageType(Enum):
	Request = 0
	Response = 1
	Auth = 2
	Error = 3
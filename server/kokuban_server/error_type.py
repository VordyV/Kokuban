from enum import Enum

class ErrorType(Enum):
	incorrect_packet_format = 0
	request_header_invalid = 1
	no_auth_data = 2
	incorrect_auth_data = 3
	re_auth = 4
	incorrect_key_hash = 5
	incorrect_profile = 6
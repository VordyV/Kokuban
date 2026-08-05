import socket
import msgspec
from kokuban_server.package_type import PackageType
from kokuban_server.package import Package


def send_package(sock: socket.socket, package: Package) -> None:
    data = msgspec.json.encode(package) + b'\n'
    sock.sendall(data)

def recv_package(sock: socket.socket) -> Package:
    buf = b''
    while True:
        chunk = sock.recv(4096)
        if not chunk:
            raise ConnectionError('Соединение разорвано')
        buf += chunk
        if b'\n' in buf:
            line, buf = buf.split(b'\n', 1)
            return Package.validate_package(line)

def main():
    host = '127.0.0.1'
    port = 8080

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((host, port))

        request = Package(
            type=PackageType.Request,
            header='auth',
            body={"agent": ""}
        )

        send_package(sock, request)
        #response = recv_package(sock)
        #print('Ответ сервера:', response)

        request = Package(
            type=PackageType.Request,
            header='info',
            body={}
        )

        send_package(sock, request)
        response = recv_package(sock)
        print('Ответ сервера:', response)

if __name__ == '__main__':
    main()
from sys import platform
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1',5672))
if result == 0:
   print("Port is open")
else:
   print("Port is not open")
sock.close()

if platform == "linux" or platform == "linux2":
    print('Linux platform detected...')
    import distro
    dist, version, codename = distro.linux_distribution()
    if dist == 'Ubuntu':
        print('Ubuntu platform detected...')

elif platform == "darwin":
    print('OS X platform detected...')
    raise NotImplementedError
elif platform == "win32":
    print('Windows platform detected...')
    raise NotImplementedError

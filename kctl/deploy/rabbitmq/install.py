from sys import platform
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('127.0.0.1', 5672))
if result == 0:
    print("Rabbitmq detected on port 5672...")
else:
    from ...utils import BOLD

    print('Rabbitmq not detected on port 5672...')

    if platform == "linux" or platform == "linux2":
        import distro

        dist, version, codename = distro.linux_distribution()
        if dist in ('Ubuntu', 'Debian'):
            print('Please install rabbitmq:\n\n' +
                  BOLD.format('sudo apt-get install rabbitmq-server -y --fix-missing'))

        elif dist in ('RHEL', 'CentOS', 'Fedora'):
            print('Please install rabbitmq:\n\n' +
                  BOLD.format('wget https://www.rabbitmq.com/releases/'
                              'rabbitmq-server/v3.6.1/rabbitmq-server-3.6.1-1.noarch.rpmn\n'
                              'sudo yum install rabbitmq-server-3.6.1-1.noarch.rpm'))
        else:
            print('Please install rabbitmq')

    elif platform == "darwin":
        print('Please install rabbitmq:\n\n' +
              BOLD.format('brew install rabbitmq'))

    elif platform == "win32":
        print('Please install rabbitmq:\n\n' +
              BOLD.format('choco install rabbitmq'))
        raise NotImplementedError

    raise SystemExit
sock.close()

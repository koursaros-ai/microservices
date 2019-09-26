from grpc_tools import protoc


def compile_messages(app_path):
    messages_path = f'{app_path}/messages'

    print(f'Compiling messages for {app_path}')

    protoc.main((
        '',
        f'-I={app_path}',
        f'--python_out={app_path}/.koursaros',
        f'{app_path}/messages.proto',
    ))

    print(f'Compiling yamls for {app_path}')
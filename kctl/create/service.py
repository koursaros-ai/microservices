
def main(args):
    from ..boilerplate import HELLO_TEMPLATE, SERVICE_TEMPLATE
    import os

    for name in args.names:
        service_path = f'./services/{name}'
        os.makedirs(service_path)

        with open(f'{service_path}/__init__.py', 'w') as fh:
            if not args.model:
                fh.write(HELLO_TEMPLATE.format(
                    service=name
                ))

        with open(f'{service_path}/service.yaml', 'w') as fh:
            fh.write(SERVICE_TEMPLATE.format(
                service=name,
                registry=args.registry,
                base_image=args.base_image,
                dependencies=args.dependencies
            ))

        print(f'Created {service_path}')
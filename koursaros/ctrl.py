from .base import Messager, SocketType, CTRL_PORT, Command
from threading import Thread
import subprocess
from hashlib import md5
import sys
import yaml as pyyaml
from collections import defaultdict
from time import time
import koursaros_pb2

LOCAL_IP = '127.0.0.1'
CHIEF_PORT = 49152
MIN_PORT = 49153
MAX_PORT = 65536


class Control(Messager):
    handler = MessageHandler()
    subprocesses = []
    ports = set(range(MIN_PORT, MAX_PORT))

    def __init__(self):
        self.socket_ctrl = self.build_socket(SocketType.REP_BIND, CTRL_PORT)
        self.app_state = defaultdict(lambda: dict(
            messages=dict(),
            pipeline_yamls=defaultdict(lambda: dict(
                last_update=0,
                string=None,
                json=None,
                hash=None,
            )),
            service_yamls=defaultdict(lambda: dict(
                last_update=0,
                string=None,
                json=None,
                hash=None,
            )),
            pipeline_states=defaultdict(lambda: dict(
                last_update=0,
                status=None,
                ip=None,
                service_states=defaultdict(lambda: dict(
                    start_time=None,
                    last_update=0,
                    subprocess=None,
                    status=None,
                    ip=None,
                    sent=0,
                    streamer_states=defaultdict(lambda: dict(
                        port_out=self.ports.pop(),
                        port_in=self.ports.pop(),
                        last_update=0,
                        subprocess=False,
                        status=None,
                        ip=None,
                    )),
                )),
            )),
        ))

    @handler.register(koursaros_pb2.ControlRequest.ApplyYamlRequest)
    def apply_yaml(self, msg: 'koursaros_pb2.Message'):
        yaml_string = msg.control_request.apply_yaml_request.yaml_string
        yaml_hash = md5(yaml_string).hexdigest()
        yaml_json = pyyaml.safe_load(yaml_string)
        name = yaml_json['name']

        if 'pipeline' in yaml_json:
            yaml_json = yaml_json['pipeline']
            yaml_state = self.app_state['pipeline_yamls'][name]

        elif 'service' in yaml_json:
            yaml_json = yaml_json['service']
            yaml_state = self.app_state['service_yamls'][name]

        else:
            return Command.ERROR

        # return error if yaml already recorded
        if yaml_hash == yaml_state['hash']:
            return Command.ERROR

        yaml_state['string'] = yaml_string
        yaml_state['json'] = yaml_json
        yaml_state['hash'] = yaml_hash
        yaml_state['last_update'] = time()

        return Command.SUCCESS

    @staticmethod
    def subprocess_call(cmd, state):
        subprocess.call(cmd)

        # once done:
        state['subprocess'] = False

    @handler.register(koursaros_pb2.ControlRequest.SubprocessRequest)
    def subprocess_pipelines(self, msg: 'koursaros_pb2.Message'):
        """
        Deploys all current yamls in subprocesses
        """
        sy = self.app_state['service_yamls']
        sd = 'Service "%s" does not have a yaml'
        rp = ('READY', 'PENDING')
        python = sys.executable
        ip = LOCAL_IP
        cmds = []

        for pipeline in self.app_state['pipeline_states'].values():
            service_states = pipeline['service_states']
            for service in service_states:

                # if service not in service yamls, fail
                if service not in sy: return Command.FAILED, sd % service

                yaml = sy[service]['json']
                service_state = service_states[service]

                # if service not running or deploying, deploy
                if service_state['status'] not in rp:
                    cmd = [python, '-m', 'koursaros.bases.%s' % yaml['base'], pipeline, service, ip]
                    cmds += (service_state, cmd)

                streamer_states = service_state['streamer_states']
                for streamer in range(yaml['streamers']):
                    streamer_state = streamer_states[streamer]

                    # if streamer not running or deploying, deploy
                    if streamer_state['status'] not in rp:
                        cmd = [python, '-m', 'koursaros.streamer', pipeline, service, streamer, ip]
                        cmds += (streamer_state, cmd)

            # run services and streamers, update states
            for state, cmd in cmds:
                t = Thread(target=self.subprocess_call, args=(cmd, state))
                self.subprocesses.append(t)
                t.start()

            return Command.SUCCESS

    @handler.register(koursaros_pb2.ControlRequest.StateUpdate)
    def state_update(self, msg: 'koursaros_pb2.Message'):

        for path, value in msg.control_request.state_update.updates:
            node = self.app_state

            for key in path[:-1]:
                node = node[key]
            node[path[-1]] = value


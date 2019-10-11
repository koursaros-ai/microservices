from .base import Messager, SocketType, CTRL_PORT, Command
from kctl.manager import AppManager
from .yamls import Yaml, YamlType
from threading import Thread, get_ident, Condition
from typing import List
import subprocess
from hashlib import md5
import atexit
import sys
import yaml as pyyaml
from json import loads


LOCAL_IP = '127.0.0.1'
CHIEF_PORT = 49152
MIN_PORT = 49153
MAX_PORT = 65536

DEFAULT_PIPELINE_STATE = dict(
    updating=False,
    services=set(),
    ip=None,
)

DEFAULT_SERVICE_STATE = dict(
    streamers=set(),
    has_yaml=False,
    is_first=False,
    is_last=False,
    subproc=False,
    deploying=False,
    running=False,
    killing=False,
    rip=False,
    ip=None,
)

DEFAULT_STREAMER_STATE = dict(
    port_in=None,
    port_out=None,
    subproc=False,
    deploying=False,
    running=False,
    killing=False,
    rip=False,
    ip=None,
)


class Chief(Messager):
    pipeline_name = dict()
    pipeline_yamls = dict()
    service_yamls = dict()
    pipeline_states = dict()
    service_states = dict()
    streamer_states = dict()
    ports = set(range(MIN_PORT, MAX_PORT))

    def __init__(self):
        self.socket_ctrl = self.build_socket(SocketType.REP_BIND, CTRL_PORT)
        self.am = AppManager()
        self.subproc_cb = Condition()

        # wait for subprocesses to finish on exit
        atexit.register(self.wait_for_subprocs)

    def apply_yaml(self, name: bytes, yaml_type: bytes, yaml_string: bytes):
        # yaml_hash = md5(yaml_string).hexdigest()
        name = name.decode()
        yaml_type = YamlType(yaml_type)
        yaml = pyyaml.safe_load(yaml_string)
        ss = self.service_states
        sy = self.service_yamls
        ps = self.pipeline_states
        py = self.pipeline_yamls
        sts = self.streamer_states

        if yaml_type == YamlType.PIPELINE:
            ps[name] = DEFAULT_PIPELINE_STATE
            py[name] = yaml

            for service in py['services']:
                if service not in ss:
                    ss[service] = DEFAULT_SERVICE_STATE
                ps[name]['services'].add(service)

            return Command.SUCCESS, 'Pipeline yaml "%s" applied' % name

        elif yaml_type == YamlType.SERVICE:
            ss[name] = DEFAULT_SERVICE_STATE

            for i in range(yaml['streamers']):
                streamer = '/%s_%s' % (name, i)
                ss[name]['streamers'].add(streamer)
                sts[streamer] = DEFAULT_STREAMER_STATE
                sts[streamer]['port_in'] = self.ports.pop()
                sts[streamer]['port_out'] = self.ports.pop()

            sy[name] = yaml
            ss[name]['has_yaml'] = True

            return Command.SUCCESS, 'Service yaml "%s" applied' % name

    def deploy_subproc(self):
        """
        Deploys all current yamls held by the chief
        """
        ps = self.pipeline_states
        ss = self.service_states
        sy = self.service_yamls
        sts = self.streamer_states
        cmds = []

        for pipeline in ps.values():
            for service in pipeline['services']:
                yaml = sy[service]
                state = ss[service]
                b = state['base']
                st = state['streamers']
                hy = state['has_yaml']
                d = state['deploying']
                r = state['running']
                s = state['subproc']
                ip = LOCAL_IP

                if not hy:
                    return Command.FAILED, 'Service "%s" does not have a yaml' % service

                if not r and not d:
                    cmd = [sys.executable, '-m', 'koursaros.bases.%s' % b, service, ip]
                    cmds += (state, cmd)

                for streamer in st:
                    state = sts[streamer]
                    d = state['deploying']
                    r = state['running']

                    if not d and not r:
                        cmd = [sys.executable, '-m', 'koursaros.streamer', streamer, ip]
                        cmds += (state, cmd)

            for state, cmd in cmds:
                self.subproc(cmd)
                state['deploying'] = True

            return Command.SUCCESS, 'Deployed pipelines'

    def status(self, name: bytes, status: bytes):
        """
        Receives status updates from the services and updates
        them with what they should be doing.

        :param name: name of the service requesting
        :param status: status update from service
        :return: service configs
        """
        name = name.decode()
        status = loads(status)
        ss = self.service_states
        sts = self.streamer_states

        if name[0] == '/':
            # (if streamer)
            state = self.service_states[name]



    def service_kill_res(self, name):
        state = self.service_states[name]

        state['killing'] = True
        state['rip'] = True

    def router_kill_res(self, name):
        state = self.service_states[name]

        state['killing'] = True
        state['rip'] = True

    def update_pipelines(self, c):
        if pipeline_name not in self.pipelines:
            c = True
            pipeline = dict()
            pipeline['services'] = dict()
        else:
            pipeline = self.pipelines[pipeline_name]

        for service_name in pipeline_yaml['services']:
            if service_name not in pipeline:
                c = True
                pipeline['services'][service_name] = dict()

        pipeline['path'] = pipeline_yaml_path
        self.pipelines[pipeline_name] = pipeline
        self.update_services(c)
        self.update_streamers(c)
        self.send(self.socket_ctrl, Command.SUCCESS, b'Deployed pipeline "%s".' % pipeline_name)

    def update_services(self, c):
        for pipeline in self.pipelines:
            for service in pipeline['services']:
                if 'process' not in service:
                    service_yaml = self.am.get_yaml_path(service, YamlType.SERVICE)
                    cmd = [sys.executable, '-m', 'koursaros.bases.%s' % service_yaml['base']]

        new_service = dict()
        service_yaml_path = self.am.get_yaml_path(service_name, YamlType.SERVICE)
        service_yaml = Yaml(service_yaml_path)
        self.save_base(service_yaml.base)

        self.subproc(cmd)
        new_service['yaml'] = service_yaml
        new_pipeline['services'][service_name] = new_service

    def save_base(self, base_name):
        base_yaml_path = self.am.get_yaml_path(base_name, YamlType.BASE)

        if self.am.is_in_app_path(base_name, YamlType.BASE):
            self.am.save_base_to_pkg(base_name)

        if base_yaml_path is None:
            raise FileNotFoundError('Could not find base "%s" base.yaml' % base_name)

    def update_streamers(self, c):
        for pipeline in self.pipelines:
            excess = len(pipeline['streamers']) - len(pipeline['services']) - 1

            for _ in range(excess):
                cmd = [sys.executable, '-m', 'koursaros.streamer']

            excess *= -1

            self.subproc(cmd, 'streamers', )

    def config(self, entity):
        pass

    def wait_for_subprocs(self):
        """
        Waits for subprocesses to finish. Add to exit stack command.
        """
        while self.subprocs:
            self.subproc_cb.acquire()
            self.subproc_cb.wait()
            self.subproc_cb.release()

    def subproc(self, cmd: List, entity, name):
        """
        Subprocess a command. Each subprocessed command is
        managed by the app manager and the stack does not exit
        until all commands finish...

        :param cmd: command to run
        """

        if not isinstance(cmd, list):
            raise TypeError('"%s" must be list type')

        t = Thread(target=self.subproc_thread, args=[cmd])

        self.subprocs.add(t.ident)
        t.start()

    def subproc_thread(self, cmd):
        subprocess.call(cmd)
        self.subprocs.discard(get_ident())
        self.subproc_cb.acquire()
        self.subproc_cb.notify()
        self.subproc_cb.release()

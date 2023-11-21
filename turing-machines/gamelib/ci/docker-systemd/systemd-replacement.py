#!/usr/bin/env python3
import sys
import os
import subprocess
import glob
import shlex
import time
import traceback
import signal
import pwd
import grp


SYSTEMD_FOLDERS = [
    '/lib/systemd/system/multi-user.target.wants/*',
    '/etc/systemd/system/*.wants/*',
    #'/lib/systemd/system/local-fs.target.wants/*',
    #'/lib/systemd/system/sockets.target.wants/*udev*',
    #'/lib/systemd/system/sockets.target.wants/*initctl*',
    #'/lib/systemd/system/sysinit.target.wants/systemd-tmpfiles-setup*',
    #'/lib/systemd/system/systemd-update-utmp*',
]


def run_generators():
    for gen in glob.glob('/lib/systemd/system-generators/*-generator'):
        try:
            print(f'Running generator script {gen} ...')
            subprocess.check_call([gen, '/etc/systemd/system', '/etc/systemd/system', '/etc/systemd/system'], timeout=5)
        except:
            traceback.print_exc()


def get_services():
    services = []
    for folder in SYSTEMD_FOLDERS:
        for file in glob.glob(folder):
            if file.endswith('.timer'):
                continue
            name = os.path.basename(file).rsplit('.', 1)[0]
            if '@' in name:
                arg = name.split('@')[1]
            else:
                arg = ''
            with open(file, 'r') as f:
                service = {'file': file, 'name': name}
                collected_prefix = ''
                for line in f.read().split('\n'):
                    line = collected_prefix  + line.strip()
                    if line and not line.startswith('#'):
                        if line.endswith('\\'):
                            collected_prefix = line[:-1]
                            continue
                        else:
                            collected_prefix = ''
                    if '=' in line:
                        k, v = line.split('=', 1)
                        v = v.replace('%i', arg)
                        k = k.strip()
                        if k == 'Environment':
                            if k not in service:
                                service[k] = []
                            service[k].append(v.strip())
                        else:
                            service[k] = v.strip()
                services.append(service)
    return services


def ignore_service(service) -> bool:
    if service['name'].startswith('systemd-'):
        return True
    if service['name'].startswith('getty'):
        return True
    if service['name'] in {'console-getty', 'remote-fs'}:
        return True
    return False


def start_service(service):
    if ignore_service(service):
        print(f'Ignoring service "{service["name"]}"')
        return
    print(f'Starting service "{service["name"]}" ({service["Description"]}) ...')
    for k, v in service.items():
        print(f'- {k}: {v}')
    opts = {'env': {k:v for k, v in os.environ.items()}}
    if 'WorkingDirectory' in service:
        opts['cwd'] = service['WorkingDirectory']
    if 'Environment' in service:
        for line in service['Environment']:
            for x in line.split(' '):
                a, b = x.split('=', 1)
                opts['env'][a] = b
    uid = 0
    gid = 0
    if service.get('User', 'root') != 'root':
        opts['user'] = service['User']
        uid = pwd.getpwnam(service['User']).pw_uid
        if 'Group' in service:
            opts['group'] = service['Group']
            gid = grp.getgrnam(service['Group']).gr_gid


    # runtime directories
    runtime_dirs = []
    if 'PIDFile' in service and service['PIDFile'].startswith('/run/'):
        runtime_dirs.append(os.path.dirname(service['PIDFile']))
    if 'RuntimeDirectory' in service:
        for d in shlex.split(service['RuntimeDirectory']):
            if d.startswith('/run/'):
                runtime_dirs.append(d)
            elif not d.startswith('/'):
                runtime_dirs.append(os.path.join('/run', d))
    for d in runtime_dirs:
        if d != '/run':
            print(f'mkdir "{d}" for {uid}:{gid}')
            os.makedirs(d, exist_ok=True)
            os.chown(d, uid, gid)
            os.chmod(d, 0o777) # workaround for postgresql

    if 'ExecStartPre' in service:
        cmd = service['ExecStartPre']
        MustSuccess = True
        while cmd[0] in '+-!:@':
            if cmd[0] == '-':
                MustSuccess = False
            cmd = cmd[1:]
        cmd = shlex.split(cmd)
        print(f'[Start pre] {cmd} {MustSuccess}')
        subprocess.run(cmd, shell=True, check=MustSuccess, timeout=15, **opts)

    if 'ExecStart' in service:
        t = service.get('Type', 'simple')
        cmd = service['ExecStart']
        while cmd[0] in '+-!:@': cmd = cmd[1:]
        # cmd = shlex.split(cmd)
        if t == 'simple' or t == 'exec' or t == 'oneshot' or t == 'notify':
            print(f'[Start simple] {cmd}')
            print(opts)
            subprocess.Popen(cmd, shell=True, **opts)
        elif t == 'forking':
            print(f'[Start forking] {cmd}')
            subprocess.run(cmd, shell=True, check=True, timeout=10, **opts)
        else:
            raise Exception(f'Invalid service type: {t}')
    else:
        print(f'[WARN] Cannot start service {repr(service["name"])}, no start command.')


def main():
    start_mode = len(sys.argv) > 2 and sys.argv[1] == 'start'

    run_generators()
    services = get_services()

    if start_mode:
        services = [s for s in services if s['name'] in sys.argv[2:]]

    for service in services:
        try:
            start_service(service)
        except:
            traceback.print_exc()
            print(f'[ERR] Could not start service {service["name"]}')

    if not start_mode:
        print('All services started.')
        while True:
            time.sleep(3600)


def terminate(signal, frame):
    print(f'Signal {signal}, terminating.')
    sys.exit(0)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, terminate)
    signal.signal(signal.SIGTERM, terminate)
    main()

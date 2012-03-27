import psutil
import socket
import json
import os
import sys
from subprocess import Popen, PIPE


class InvalidPIDError(StandardError):
    pass


class OSXPermissionFailure(StandardError):
    pass


def check_osx_perm():
    """
    psutil can't do the right thing on OSX because of weird permissioning rules
    in Darwin.

    http://code.google.com/p/psutil/issues/detail?id=108
    """
    return 'darwin' not in sys.platform or os.getuid() == 0


def supports_iocounters():
    if not hasattr(psutil.Process, 'get_io_counters') or os.name != 'posix':
        return False
    return True


class LazyPSUtil(object):
    """
    This class can only be used *outside* the process that is being inspected
    """
    POLL_INTERVAL = 1.0

    def __init__(self, pid):
        self.pid = pid
        self._process = None

        # Delete any methods that we don't support on the current platform
        if not supports_iocounters():
            del self.__class__.get_io_counters

        if not check_osx_perm():
            del self.__class__.get_cpu_info
            del self.__class__.get_memory_info
            del self.__class__.get_thread_cpuinfo

    @property
    def process(self):
        if self._process is None:
            self._process = psutil.Process(self.pid)
            if os.getpid() == self.pid:
                raise InvalidPIDError("Can't run process inspection on itself")
        return self._process

    def get_connections(self):
        connections = []
        for conn in self.process.get_connections():
            if conn.type == socket.SOCK_STREAM:
                type = 'TCP'
            elif conn.type == socket.SOCK_DGRAM:
                type = 'UDP'
            else:
                type = 'UNIX'
            lip, lport = conn.local_address
            if not conn.remote_address:
                rip = rport = '*'
            else:
                rip, rport = conn.remote_address
            connections.append({
                'type': type,
                'status': conn.status,
                'local': '%s:%s' % (lip, lport),
                'remote': '%s:%s' % (rip, rport),
                })
        return connections

    def get_io_counters(self):
        if not supports_iocounters():
            sys.exit('platform not supported')

        io = self.process.get_io_counters()

        return {'read_bytes': io.read_bytes,
                'write_bytes': io.write_bytes,
                'read_count': io.read_count,
                'write_count': io.write_count,
                }

    def get_memory_info(self):
        if not check_osx_perm():
            raise OSXPermissionFailure("OSX requires root for memory info")

        cputimes = self.process.get_cpu_times()
        meminfo = self.process.get_memory_info()
        mem_details = {'pcnt': self.process.get_memory_percent(),
                'rss': meminfo.rss,
                'vms': cputimes.system}
        return mem_details

    def get_cpu_info(self):
        if not check_osx_perm():
            raise OSXPermissionFailure("OSX requires root for memory info")

        cputimes = self.process.get_cpu_times()
        cpu_pcnt = self.process.get_cpu_percent(interval=self.POLL_INTERVAL)
        return {'cpu_pcnt': cpu_pcnt,
                'cpu_user': cputimes.user,
                'cpu_sys': cputimes.system}

    def get_thread_cpuinfo(self):
        if not check_osx_perm():
            raise OSXPermissionFailure("OSX requires root for memory info")

        thread_details = {}
        for thread in self.process.get_threads():
            thread_details[thread.id] = {'sys': thread.system_time,
                    'user': thread.user_time}
        return thread_details

    def write_json(self, net=False, io=False, cpu=False, mem=False, threads=False):
        data = {}

        if net:
            data['net'] = self.get_connections()

        if io:
            data['io'] = self.get_io_counters()

        if cpu:
            data['cpu'] = self.get_cpu_info()

        if mem:
            data['mem'] = self.get_memory_info()

        if threads:
            data['threads'] = self.get_thread_cpuinfo()

        sys.stdout.write(json.dumps(data))
        sys.stdout.flush()


def process_details(pid=None, net=False, io=False,
                    cpu=False, mem=False, threads=False):
    """
    psutils doesn't work on it's own process.  Run psutils through a subprocess
    so that we don't have to deal with the process issues
    """
    if pid is None:
        pid = os.getpid()
    interp = sys.executable
    cmd = ['from pslogtools import LazyPSUtil',
           'LazyPSUtil(%(pid)d).write_json(net=%(net)s, io=%(io)s, cpu=%(cpu)s, mem=%(mem)s, threads=%(threads)s)']
    cmd = ';'.join(cmd)
    rdict = {'pid': pid,
            'net': int(net),
            'io': int(io),
            'cpu': int(cpu),
            'mem': int(mem),
            'threads': int(threads)}
    cmd = cmd % rdict
    proc = Popen([interp, '-c', cmd], stdout=PIPE, stderr=PIPE)
    result = proc.communicate()
    stdout, stderr = result[0], result[1]
    return json.loads(stdout)

def metlog_procinfo(self, pid, config):
    '''
    This is a metlog extension method to place process data into the metlog
    fields dictionary
    '''
    if pid is None:
        pid = os.getpid()

    net = config.pop('net', False)
    io = config.pop('io', False)
    cpu = config.pop('cpu', False)
    mem = config.pop('mem', False)
    threads = config.pop('threads', False)
    if config:
        raise SyntaxError('Invalid arguments: %s' % str(config))

    fields = process_details(pid, net, io, cpu, mem, threads)
    self.metlog('procinfo', fields=fields)


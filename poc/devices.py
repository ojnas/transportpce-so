#!/usr/bin/env python

import docker
                        
class DockerDevices():
    
    def __init__(self, devices):
        self.devices = devices
        self.started_containers = []
    
    def start(self):
        client = docker.from_env()
        for dev in self.devices:
            self.started_containers.append(client.containers.run("confd-openroadm", dev, init=True, detach=True, tty=True, remove=True))

    def get_ip_addrs(self):
        for container in self.started_containers:
            container.reload()
        return [container.attrs["NetworkSettings"]["IPAddress"] for container in self.started_containers]
           
    def stop(self):
        for container in self.started_containers:
            container.stop()
        self.started_containers = []
        
    def save_traces(self):
        for container, dev in zip(self.started_containers, self.devices):
            bits, stat = container.get_archive('/confd/var/confd/log/netconf.trace')
            with open(dev+'.tar', 'wb') as f:
                for chunk in bits:
                    f.write(chunk)

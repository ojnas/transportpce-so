#!/usr/bin/env python

import docker
                        
class DockerDevices():
    
    started_containers = []
    
    def start(self, devices):
        client = docker.from_env()
        for dev in devices:
            self.started_containers.append(client.containers.run("confd-openroadm", dev, init=True, detach=True, tty=True, remove=True))

    def get_ip_addrs(self):
        for container in self.started_containers:
            container.reload()
        return [container.attrs["NetworkSettings"]["IPAddress"] for container in self.started_containers]
           
    def stop(self):
        for container in self.started_containers:
            container.stop()
        self.started_containers = []

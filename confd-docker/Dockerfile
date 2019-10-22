FROM ubuntu:18.04
RUN apt-get update && apt-get install -y libssl-dev libssl1.0.0 openssh-client

ARG CONFD_INSTALLER=confd-basic-7.2.0.1.linux.x86_64.installer.bin

# Install ConfD in the container
COPY $CONFD_INSTALLER /tmp
RUN /tmp/$CONFD_INSTALLER /confd && \
    rm -rf /confd/etc/confd/tailf-netconf-with-transaction-id.fxs /tmp/*
COPY confd.conf /confd/etc/confd

# Copy OpenROADM yang models, initial config and start scripts
COPY openroadm /openroadm
ENV PATH=/openroadm/start-scripts:$PATH

# Compile YANG-models
RUN cd /openroadm/yang-models && \
    for f in *.yang; do /confd/bin/confdc -c $f; done && \
    rm *.yang

# Expose netconf port
EXPOSE 2022

CMD ["/bin/bash"]

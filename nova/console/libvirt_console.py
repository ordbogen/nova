# Copyright (c) 2016 Ordbogen A/S
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Console daemon for libvirt"""

import libvirt
import socket

from oslo_log import log as logging

LOG = logging.getLogger(__name__)

class LibvirtConsole(object):
    def __init__(self, uri, domain_name, listen, port):
        self.uri = uri
        self.domain_name = domain_name
        self.listen = listen
        self.port = port

        self._server_sock = None
        self._session_sock = None

        self._conn = None
        self._domain = None
        self._stream = None
        self._console = None

        self._running = True

    def _create_server(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.listen, self.port))
        sock.listen(127)

        self._server_sock = sock
        libvirt.virEventAddHandle(sock.fileno(),
                                  libvirt.VIR_EVENT_HANDLE_READABLE,
                                  self._on_incoming_connection,
                                  self)

    def _connect_to_console(self):
        try:
            self._conn = libvirt.open(self.uri)
            self._domain = self._conn.lookupByName(self.domain_name)
            self._stream = self._conn.newStream(libvirt.VIR_STREAM_NONBLOCK)
            self._console = self._domain.openConsole(None, self._stream, 0)

            self._strem.eventAddCallback(libvirt.VIR_STREAM_EVENT_READABLE,
                                         self._on_stream_data,
                                         self)
            return True
        except libvirt.libvirtError as e:
            LOG.warn(e.format_message())
            return False

    @staticmethod
    def _on_incoming_connection(watch, fd, events, self):
        sock, addr = self._server_sock.accept()

        if self._session_sock is not None:
            sock.sendall("Console already active on another session\n")
            sock.close()
        elif self._connect_to_console():
            sock.setblocking(False)
            self._session_sock = sock
            libvirt.virEventAddHandle(sock.fileno(),
                                      libvirt.VIR_EVENT_HANDLE_READABLE,
                                      self._on_socket_data,
                                      self)
        else:
            sock.sendall("Failed to establish connection to console\n")
            sock.close()
            self._terminate()

    @staticmethod
    def _on_socket_data(watch, fd, events, self):
        chunk = self._session_sock.recv(1024)
        if len(chunk) == 0:
            self._terminate()
        else:
            self._stream.send(chunk)

    @staticmethod
    def _on_stream_data(stream, events, self):
        chunk = self._stream.recv(1024)
        self._session_sock.sendall(chunk)

    def _terminate(self):
        self._running = False

    def _run_event_loop(self):
        while self._running:
            libvirt.virEventRunDefaultImpl()

    def run(self):
        libvirt.virEventRegisterDefaultImpl()
        self._create_server()
        self._run_event_loop()

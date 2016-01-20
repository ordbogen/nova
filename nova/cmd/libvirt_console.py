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

import sys

from oslo_config import cfg
from oslo_log import log as logging
from oslo_reports import guru_meditation_report as gmr

from nova import config
from nova import version
from nova.console import libvirt_console

opts = [
    cfg.StrOpt("uri",
                  help="Libvirt URI to connect to"),
    cfg.StrOpt("domain",
                  help="Libvirt domain to access"),
    cfg.StrOpt("bind",
                  default="0.0.0.0",
                  help="Address on which to listen for incoming connections"),
    cfg.IntOpt("port",
                  min=1,
                  max=65535,
                  help="Port on which to listen for incoming connections")
    ]

CONF = cfg.CONF
CONF.register_cli_opts(opts, group="libvirt_console")

def main():
    config.parse_args(sys.argv)
    logging.setup(CONF, "nova")

    gmr.TextGuruMeditation.setup_autorun(version)

    console = libvirt_console.LibvirtConsole(CONF.libvirt_console.uri,
                                             CONF.libvirt_console.domain,
                                             CONF.libvirt_console.bind,
                                             CONF.libvirt_console.port)
    console.run()

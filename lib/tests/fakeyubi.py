#
#   Copyright (c) 2018-2019 One Identity
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
import os
import sys
import socket


class FakeYubikeyService(object):
    def __init__(self, watcher_getter, port_getter):
        self._watcher_getter = watcher_getter
        self._port_getter = port_getter
        self.server_url = None

    def run(self):
        host = "localhost"
        port = self._port_getter()
        self.server_url = "http://{}:{}".format(host, port)

        testdir = os.path.dirname(os.path.abspath(__file__))
        script = "{}/mock_http_server.py".format(testdir)

        def checker():
            try:
                socket.create_connection((host, port))
            except socket.error:
                return False
            return True

        self._watcher_getter(name=sys.executable, arguments=[script, "--port", str(port)], checker=checker)

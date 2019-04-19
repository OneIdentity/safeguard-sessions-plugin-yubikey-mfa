#!/usr/bin/env python
# Copyright (c) 2010-2015, Tomaz Muraus
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the Tomaz Muraus nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL Tomaz Muraus BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# One Identity: This file is part of yubico-client's test suite.
#   This file is only used in testing, not bundled in plugin release.
#
# Downloaded from:
# https://raw.githubusercontent.com/Kami/python-yubico-client/master/tests/mock_http_server.py
import os
import time
import sys
from yubico_client.yubico import BAD_STATUS_CODES
from yubico_client.py3 import b
from optparse import OptionParser
from os.path import join as pjoin

try:
    import BaseHTTPServer
    BaseHTTPRequestHandler = BaseHTTPServer.BaseHTTPRequestHandler
    server_class = BaseHTTPServer.HTTPServer
except ImportError:
    from http.server import HTTPServer as BaseHTTPServer
    from http.server import BaseHTTPRequestHandler
    server_class = BaseHTTPServer

sys.path.append(pjoin(os.path.dirname(__file__), '../'))

mock_action = None
signature = None


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        global mock_action, signature

        if self.path.find('?') != -1:
            self.path, self.query_string = self.path.split('?', 1)
            split = self.query_string.split('&')
            self.query_string = dict([pair.split('=', 1) for pair in split])

        else:
            self.query_string = {}

        if self.path == '/set_mock_action':
            action = self.query_string['action']

            if 'signature' in self.query_string:
                signature = self.query_string['signature']
            else:
                signature = None

            print('Setting mock_action to %s' % (action))
            mock_action = action
            self._end(status_code=200)
            return

        if mock_action in BAD_STATUS_CODES:
            return self._send_status(status=mock_action)
        elif mock_action == 'no_such_client':
            return self._send_status(status='NO_SUCH_CLIENT')
        elif mock_action == 'no_signature_ok':
            return self._send_status(status='OK')
        elif mock_action == 'ok_signature':
            return self._send_status(status='OK',
                                     signature=signature)
        elif mock_action == 'no_signature_ok_invalid_otp_in_response':
            return self._send_status(status='OK',
                                     signature=signature, otp='different')
        elif mock_action == 'no_signature_ok_invalid_nonce_in_response':
            return self._send_status(status='OK',
                                     signature=signature, nonce='different')
        elif mock_action == 'timeout':
            time.sleep(1)
            return self._send_status(status='OK')
        else:
            self._end(status_code=500)
            return

    def _end(self, status_code=200, body=''):
        print('Sending response: status_code=%s, body=%s' %
              (status_code, body))
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/plain')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(b(body))

    def _send_status(self, status, signature=None, otp=None, nonce=None):
        if signature:
            body = '\nh=%s\nstatus=%s' % (signature, status)
        else:
            body = 'status=%s' % (status)

        if otp:
            body += '&otp=%s' % (otp)

        if nonce:
            body += '&nonce=%s' % (nonce)

        self._end(body=b(body))


def main():
    usage = 'usage: %prog --port=<port>'
    parser = OptionParser(usage=usage)
    parser.add_option('--port', dest='port', default=8881,
                      help='Port to listen on', metavar='PORT')

    (options, args) = parser.parse_args()

    httpd = server_class(('127.0.0.1', int(options.port)), Handler)
    print('Mock API server listening on 127.0.0.1:%s' % (options.port))

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

    httpd.server_close()


main()

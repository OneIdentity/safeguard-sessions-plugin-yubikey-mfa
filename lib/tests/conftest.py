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
import pytest
from ..client import Client
import requests
from .fakeyubi import FakeYubikeyService

random = '\x81\x85\x15\n8\xcc\xc6\xeac\xe6\x1c\xe5\x07"\x91\x08G\xa8\x02\xdd}\xde\x96\xad\xd9\x95\xde\x19\xf4P'


#
# We can optionally run a mock HTTP server, supplied by Yubikey when testing
# this module.  We actually record requests/responses to this server when
# doing our own "check-replay" kind of testing.
#
# This fixture starts that process via the FakeYubikeyService class and
# returns the URL where it listens.
#
@pytest.fixture(scope="session")
def fake_yubikey_service(request, watcher_getter, port_getter):
    service = FakeYubikeyService(watcher_getter, port_getter)
    service.run()
    return service.server_url


#
# Since the request/response includes a random nonce, that would change
# every invocation.  To stop that from happening, always use the same random
# string.
#
@pytest.fixture
def fake_random(monkeypatch):
    monkeypatch.setattr('os.urandom', lambda len: random)


@pytest.fixture
def yubi_server_url(request):
    backend_service = request.config.getoption('backend_service')

    if backend_service in ("record", "use"):
        return request.getfixturevalue('fake_yubikey_service')
    elif backend_service == "replay":
        vcr_cassette = request.getfixturevalue('vcr_cassette')
        return _peek_server_in_recorded_requests(vcr_cassette)


@pytest.fixture
def yubi_action(yubi_server_url):
    def _(action):
        requests.get('{}/set_mock_action?action={}'.format(yubi_server_url, action))
    return _


@pytest.fixture
def yubi_trigger_timeout(yubi_action):
    yubi_action('timeout')


@pytest.fixture
def yubi_trigger_badotp(yubi_action):
    yubi_action('BAD_OTP')


@pytest.fixture
def yubi_trigger_nosignok(yubi_action):
    yubi_action('no_signature_ok')


@pytest.fixture
def yubi_client(request, yubi_server_url, site_parameters):
    backend_service = request.config.getoption('backend_service')

    if backend_service != "use":
        request.getfixturevalue('fake_random')

    return Client(site_parameters['client_id'], apiurls=['{}/sapi/2.0/verify'.format(yubi_server_url)])


@pytest.fixture
def yubi_device_id(site_parameters):
    return site_parameters['device_id']


@pytest.fixture
def yubi_otp(site_parameters):
    return site_parameters['otp']


def _peek_server_in_recorded_requests(vcr_cassette):
    if len(vcr_cassette) == 0:
        return "http://definitely-unreachable-server-as-no-recordings-took-place"
    request, response = vcr_cassette.data[0]
    return 'http://{}:{}'.format(request.host, request.port)

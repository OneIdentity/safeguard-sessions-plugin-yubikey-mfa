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
from requests.exceptions import RequestException
from safeguard.sessions.plugin.mfa_client import MFAAuthenticationFailure, MFACommunicationError, MFAServiceUnreachable
from unittest.mock import MagicMock



def test_otp_ok(yubi_client, yubi_trigger_nosignok, yubi_device_id, yubi_otp):
    assert yubi_client.otp_authenticate(yubi_device_id, yubi_otp)


def test_otp_username_mismatch(yubi_client, yubi_otp):
    with pytest.raises(MFAAuthenticationFailure) as e:
        yubi_client.otp_authenticate('fakedevice', yubi_otp)

    assert e.match('User/device pair mismatch')


def test_invalid_otp(yubi_client, yubi_device_id):
    with pytest.raises(MFAAuthenticationFailure) as e:
        yubi_client.otp_authenticate(yubi_device_id, 'fakeotp')

    assert e.match('Invalid OTP format')


def test_otp_invalid_signature(yubi_client, yubi_device_id, yubi_otp):
    with pytest.raises(MFAAuthenticationFailure) as e:
        yubi_client.client.key = 'invalid key'.encode()
        yubi_client.otp_authenticate(yubi_device_id, yubi_otp)

    assert e.match('signature verification failed')


def test_otp_failed(yubi_client, yubi_trigger_badotp, yubi_device_id, yubi_otp):
    with pytest.raises(MFACommunicationError) as e:
        yubi_client.otp_authenticate(yubi_device_id, yubi_otp)

    assert e.match('NO_VALID_ANSWERS')


def test_otp_timeout(yubi_client, yubi_trigger_timeout, yubi_device_id, yubi_otp):

    yubi_client.client.DEFAULT_TIMEOUT = 0.1
    yubi_client.otp_authenticate(yubi_device_id, yubi_otp)


def test_otp_unhandled_exception(monkeypatch, yubi_device_id, yubi_otp):
    mock = MagicMock()
    monkeypatch.setattr('yubico_client.yubico.Yubico.verify', mock)
    mock.side_effect = Exception('Unhandled')
    with pytest.raises(Exception) as e:
        yubi_client = Client('clientid')
        yubi_client.otp_authenticate(yubi_device_id, yubi_otp)

    assert e.match('Unhandled')


def test_otp_requests_exception(monkeypatch, yubi_device_id, yubi_otp):
    mock = MagicMock()
    monkeypatch.setattr('yubico_client.yubico.Yubico.verify', mock)
    mock.side_effect = RequestException()
    with pytest.raises(MFAServiceUnreachable):
        yubi_client = Client('clientid')
        yubi_client.otp_authenticate(yubi_device_id, yubi_otp)


def test_no_push(yubi_client):
    with pytest.raises(MFAAuthenticationFailure) as e:
        yubi_client.push_authenticate('username')

    assert e.match('OTP required')

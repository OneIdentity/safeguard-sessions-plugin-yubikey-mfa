#
#   Copyright (c) 2018 One Identity
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
import logging
from yubico_client.yubico import Yubico, DEFAULT_API_URLS
from yubico_client.yubico_exceptions import YubicoError
from yubico_client.modhex import translate
from requests.exceptions import RequestException
from safeguard.sessions.plugin.mfa_client import (
    MFAClient,
    MFAAuthenticationFailure,
    MFACommunicationError,
    MFAServiceUnreachable,
)

logger = logging.getLogger(__name__)


class Client(MFAClient):
    def __init__(self, clientid, apikey=None, apiurls=None, timeout=None):
        super().__init__("SPS Yubikey plugin")

        self.client = Yubico(clientid, apikey, api_urls=(apiurls or DEFAULT_API_URLS))
        self.timeout = timeout

        logger.debug("Initialized")

    @classmethod
    def from_config(cls, plugin_configuration):
        apiurls = plugin_configuration.get("yubikey", "api_urls")
        if apiurls:
            apiurls = [url.strip() for url in apiurls.split(",")]

        return cls(
            clientid=plugin_configuration.get("yubikey", "client_id", required=True),
            apikey=plugin_configuration.get("yubikey", "api_key"),
            apiurls=apiurls,
            timeout=plugin_configuration.getint("yubikey", "timeout", 10),
        )

    def otp_authenticate(self, username, otp):
        logger.debug("Authenticating user: {} and OTP: {}".format(username, otp))
        modhex = translate(otp)
        if not modhex or len(modhex.pop()) != 44:
            raise MFAAuthenticationFailure("Invalid OTP format")

        deviceid = otp[:12]
        if username != deviceid:
            raise MFAAuthenticationFailure("User/device pair mismatch {} != {}".format(username, deviceid))

        try:
            logger.debug("Attempting API call")
            response = self.client.verify(otp, timeout=self.timeout)
            logger.info("API call successful")
        except YubicoError as e:
            raise MFAAuthenticationFailure(str(e))
        except RequestException as e:
            raise MFAServiceUnreachable(str(e))
        except Exception as e:
            if "NO_VALID_ANSWERS" in str(e):
                raise MFACommunicationError(str(e))
            else:
                raise

        return response == True  # noqa: E712

    def push_authenticate(self, username):
        logger.warning("Push authentication is not supported")
        raise MFAAuthenticationFailure("OTP required")

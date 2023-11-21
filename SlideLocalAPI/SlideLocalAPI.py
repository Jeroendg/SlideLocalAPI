import json
import logging
import urllib
from urllib import request, parse

_LOGGER = logging.getLogger(__name__)

URI_PREFIX = "/rpc/Slide."
DEFAULT_TIMEOUT = 10

class SlideLocal:
	#Class for Slide devices

	def __init__(self, host, id, timeout=DEFAULT_TIMEOUT, prefix=URI_PREFIX):
		self._host = host
		self._id = id
		self._timeout = timeout
		self._prefix = prefix
		self._cnoncecount = 0
		self._requestcount = 0
		self._slides = {}

	async def _make_request(self, resource):
		#Handle HTTP requests

		self._requestcount += 1
		if self._requestcount > 99999:
			self._requestcount = 1

		_LOGGER.debug(
            "REQ-L%d: data=%s",
            self._requestcount,
            resource,
        )

		response_code = resource.getcode()

		if response_code == 200:
			try:
				response = resource.read().decode('utf-8')

				try:
					json_response = json.loads(response)
				except json.decoder.JSONDecodeError:
					_LOGGER.error("RES-L%d: INVALID JSON=%s", self._requestcount, response)
					json_response = None

				return response_code, json_response

			except urllib.error.HTTPError:
				_LOGGER.error("RES-L%d: HTTP Error=%s", self._requestcount, response)
				json_response = None

		else:
			_LOGGER.error("RES-L%d: HTTPCode=%s, Data=%s", self._requestcount, response_code)
			return response_code, None

	async def _request(self, uri, data=None):
		url = "http://" + self._host + self._prefix + uri
		timeout = self._timeout
		resource = urllib.request.urlopen(url, data, timeout)
		response_code, response = await self._make_request(resource)
		return response

	async def slide_get_info(self):
		#Fetch Slide information
		result = await self._request("GetInfo")
		return result

	async def slide_get_pos(self):
		#Get Slide Position
		result = await self.slide_get_info()
		if result:
			if "pos" in result:
				return result["pos"]

			_LOGGER.error("SlideGetPosition: Missing key 'pos' in JSON=%s", json.dumps(result))
		return None

	async def slide_set_pos(self, pos):
		#Set Slide position
		try:
			set_pos = float(pos)
		except ValueError:
			_LOGGER.error("SlideSetPosition: '%s' has to be numeric", pos)
			return False

		if set_pos < 0:
			set_pos = 0
		if set_pos > 1:
			set_pos = 1

		str_pos = str(set_pos)

		data = bytes("{\"pos\": " + str_pos + "}", 'utf-8')

		response = await self._request("SetPos", data)
		return bool(response)

	async def slide_open(self):
		#Open Slide
		response = await self.slide_set_pos(0)
		return bool(response)

	async def slide_close(self):
		#Close Slide
		response = await self.slide_set_pos(1)
		return bool(response)

	async def slide_stop(self):
		#Stop Slide
		response = await self._request("Stop")
		return bool(response)

	async def  slide_calibrate(self):
		#Get starting position
		#start = self.slide_get_pos()

		#Calibrate Slide
		response = await self._request("Calibrate")
		return bool(response)

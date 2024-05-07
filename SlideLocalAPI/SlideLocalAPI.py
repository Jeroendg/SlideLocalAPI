import aiohttp
import asyncio
import json
import logging

_LOGGER = logging.getLogger(__name__)

URI_PREFIX = "/rpc/Slide."
DEFAULT_TIMEOUT = 10
POS_MIN = 0
POS_MAX = 1

class ClientConnectionError(Exception):
    """Error to indicate to connection issues with the Slide API."""

    pass


class ClientTimeoutError(Exception):
    """Error to indicate to timeout issues with the Slide API."""

    pass

class SlideLocal:
	"""Class for Slide devices"""

	def __init__(self, host, id, timeout=DEFAULT_TIMEOUT, prefix=URI_PREFIX):
		self._host = host
		self._id = id
		self._timeout = timeout
		self._prefix = prefix
		self._cnoncecount = 0
		self._requestcount = 0

	async def _request(self, uri, data=None):
		"""Handle HTTP requests"""

		# Increment request counter
		self._requestcount += 1
		if self._requestcount > 99999:
			self._requestcount = 1

		# Build request URL and set timeout
		url = "http://" + self._host + self._prefix + uri
		timeout = self._timeout

		# Request data from Slide
		try:
			async with aiohttp.request("POST", url, data=data) as response:
				# Check if request was succesful
				if response.status == 200:
					response_data = await response.text()
					# Log succesful request
					_LOGGER.debug(
						"RES-C%d: URL=%s, HTTPCode=%s, Data=%s",
						self._requestcount,
						url,
						response.status,
						response_data,
						)

					# Decode data from request
					try:
						json_data = json.loads(response_data)
					except json.decoder.JSONDecodeError:
						# Log invalid JSON error
						_LOGGER.error(
							"RES-L%d: URL=%s, INVALID JSON=%s",
							self._requestcount,
							url,
							response_data,
						)
						json_data = None

					return json_data
				# Error 401, API version on slide is possibly out of date or Local API is not active
				elif response.status == 401:
					response_data = await response.text()
					# Log error 401
					_LOGGER.error(
						"RES-L%d: URL=%s, HTTPCode=%s, Data=%s",
						self._requestcount,
						url,
						response.status,
						response_data,
					)
					_LOGGER.error(
						"Make sure the Local API is active on your Slide and up-to-date. Contact Slide support if your device needs updating."
					)
				# Log all other response codes
				else:
					response_data = await response.text()
					_LOGGER.error(
						"RES-L%d: URL=%s, HTTPCode=%s, Data=%s",
						self._requestcount,
						url,
						response.status,
						response_data,
					)

				return None
		except (
			aiohttp.client_exceptions.ClientConnectionError,
			aiohttp.client_exceptions.ClientConnectorError,
		) as err:
			raise ClientConnectionError(str(err)) from None
		except asyncio.TimeoutError as err:
			raise ClientTimeoutError("Connection Timeout") from None


	async def slide_get_info(self):
		"""Fetch the Slide information."""
		result = await self._request("GetInfo")
		return result

	async def slide_get_pos(self):
		"""Get the current position of the Slide."""
		result = await self.slide_get_info()

		# Check if there is a valid position in the data
		if result:
			if "pos" in result:
				return result["pos"]
			else:
				# Log position error
				_LOGGER.error(
					"SlideGetPosition: Missing key 'pos' in JSON=%s",
					json.dumps(result),
				)
				return None

	async def slide_set_pos(self, pos):
		"""Set a new position on the Slide."""

		# Verify that position is numeric
		try:
			set_pos = float(pos)
		except ValueError:
			_LOGGER.error(
				"SlideSetPosition: '%s' has to be numeric",
				pos,
			)
			return False

		# Make sure the position is within bounds, correct if necessary
		set_pos = max(POS_MIN, min(POS_MAX, set_pos))

		# Build the data for the request
		data = json.dumps({"pos": set_pos}).encode('utf-8')

		# Execute the request
		response = await self._request("SetPos", data)
		return bool(response)

	async def slide_open(self):
		"""Open the Slide"""
		response = await self.slide_set_pos(0)
		return bool(response)

	async def slide_close(self):
		"""Close the Slide"""
		response = await self.slide_set_pos(1)
		return bool(response)

	async def slide_stop(self):
		"""Stop the Slide immediately"""
		response = await self._request("Stop")
		return bool(response)

	async def  slide_calibrate(self):
		"""Calibrate the slide"""
		response = await self._request("Calibrate")
		return bool(response)

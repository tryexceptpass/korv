import asyncio
import asyncssh

import sys
from threading import Thread

import time
import json
import logging
import gzip


class _SSHClient(asyncssh.SSHClient):
    def connection_made(self, conn):
        logging.debug(f"Connection made to conn.get_extra_info('peername')[0]")

    def auth_completed(self):
        logging.debug('Authentication successful')


class _SSHClientSession(asyncssh.SSHTCPSession):

    def connection_made(self, chan):
        logging.debug("Session opened")
        self._chan = chan
        self._requests = dict()

    def connection_lost(self, exc):
        logging.debug("Connection lost")
        logging.debug(f"{exc}")

    def session_started(self):
        logging.debug("Session successful")

    def data_received(self, data, datatype):
        logging.debug(f"Received data: {data}")

        try:
            data = json.loads(gzip.decompress(data).decode('utf-8'))

            if data['request_id'] in self._requests:
                if callable(self._requests[data['request_id']]):
                    self._requests[data['request_id']](data)

                if self._requests[data['request_id']] is None:
                    self._requests[data['request_id']] = data
                else:
                    del(self._requests[data['request_id']])

        except Exception:
            logging.exception(f"There was an error processing the server response")

    def eof_received(self):
        logging.debug("Received EOF")
        self._chan.exit(0)

    async def send_request(self, verb, resource, body, callback):
        if verb not in ['GET', 'STORE', 'UPDATE', 'DELETE']:
            raise ValueError("Unknown verb")

        request = {
            'id': time.time(),
            'verb': verb,
            'resource': resource,
            'body': body
        }

        self._requests[request['id']] = callback
        self._chan.write(gzip.compress(json.dumps(request, separators=[',', ':']).encode('utf-8')))
        logging.debug(f"{verb} {resource} {body}")

        return request['id']


class KorvClient:

    def __init__(self, host='localhost', port=8022, client_keys=None, known_hosts=None, max_packet_size=32768):
        self.max_packet_size = max_packet_size

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._session = asyncio.get_event_loop().run_until_complete(self.__connect(host, port, known_hosts, client_keys))

        try:
            t = Thread(target=self.__start_loop, args=(self._loop,))
            t.start()
            # asyncio.run_coroutine_threadsafe(self.__connect(), self._loop)

        except (OSError, asyncssh.Error) as exc:
            sys.exit(f'SSH connection failed: {exc}')

    def __start_loop(self, loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    async def __connect(self, host, port, known_hosts, client_keys):
        logging.info(f"Connecting to SSH Server {host}:{port}")
        conn, client = await asyncssh.create_connection(
            _SSHClient,
            host,
            port,
            client_keys=client_keys,
            known_hosts=known_hosts
        )

        logging.debug("Opening Socket")
        chan, session = await conn.create_connection(_SSHClientSession, host, port, max_pktsize=self.max_packet_size)
        return session

    def get(self, resource, body=None, callback=None):
        if callback is None:
            request_id = asyncio.run_coroutine_threadsafe(self._session.send_request("GET", resource, body, None), self._loop).result()

            while self._session._requests[request_id] is None:
                time.sleep(0.1)

            response = self._session._requests[request_id]
            del(self._session._requests[request_id])

            return response
        else:
            asyncio.run_coroutine_threadsafe(self._session.send_request("GET", resource, body, callback), self._loop)

    def store(self, resource, body, callback=None):
        asyncio.run_coroutine_threadsafe(self._session.send_request("STORE", resource, body, callback), self._loop)

    def update(self, resource, body, callback=None):
        asyncio.run_coroutine_threadsafe(self._session.send_request("UPDATE", resource, body, callback), self._loop)

    def delete(self, resource, body=None, callback=None):
        asyncio.run_coroutine_threadsafe(self._session.send_request("DELETE", resource, body, callback), self._loop)

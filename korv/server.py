import asyncio
import asyncssh
import logging

import sys
import traceback
import time
import json


class _KorvServerSession(asyncssh.SSHTCPSession):
    def __init__(self, callbacks):
        self._callbacks = callbacks

    def connection_made(self, chan):
        """New connection established"""

        logging.info("Connection incoming")
        self._chan = chan

    def connection_lost(self, exc):
        """Lost the connection to the client"""

        logging.info("Connection lost")
        logging.info(f"{exc}")

    def session_started(self):
        """New session established succesfully"""

        logging.info("Connection successful")

    def data_received(self, data, datatype):
        """New data coming in"""

        logging.info(f"Received data: {data}")
        self._dispatch(data)

    def eof_received(self):
        """Got an EOF, close the channel"""

        logging.info("EOF")
        self._chan.exit(0)

    def _dispatch(self, data):
        try:
            request = json.loads(data.decode('utf-8'))
            if 'id' not in request:
                logging.info("Malformed request: missing 'id'")
                self._send_response(0, 400, {"message": "Missing 'id'"})

            if 'verb' not in request:
                logging.info("Malformed request: missing 'request'")
                self._send_response(request['id'], 400, {"message": "Missing 'verb'"})

            if 'resource' not in request:
                logging.info("Malformed request: missing 'resource'")
                self._send_response(request['id'], 400, {"message": "Missing 'resource'"})

            if request['verb'] == 'STORE' and 'body' not in request['request']:
                logging.info("Malformed request: missing 'resource'")
                self._send_response(request['id'], 400, {"message": "Missing 'body'"})

            elif request['verb'] == 'UPDATE' and 'body' not in request['request']:
                logging.info("Malformed request: missing 'resource'")
                self._send_response(request['id'], 400, {"message": "Missing 'body'"})

        except Exception as e:
            logging.info("Unable to process request")
            self._send_response(0, 400, {"message": "Unable to process request"})

        self.__process_request(request)

    def __process_request(self, request):
        if request['verb'] not in self._callbacks:
            logging.info(f"No callback found for {request['verb']}")
            self._send_response(request['id'], 404)
            return

        if request['resource'] not in self._callbacks[request['verb']]:
            logging.info(f"No callback found for {request['verb']} on {request['resource']}")
            self._send_response(request['id'], 404)
            return

        for callback in self._callbacks[request['verb']][request['resource']]:
            try:
                self._send_response(request['id'], *callback(request))

            except Exception as e:
                logging.info(f"Internal error when executing {request['verb']} on {request['resource']}")
                self._send_response(request['id'], 500, {"message": str(e), "traceback": traceback.format_exc()})

    def _send_response(self, request_id, code, body=None):
        """Send a response to the given client request"""

        cmd = {
            'id': time.time(),
            'request_id': request_id,
            'code': code,
            'body': body
        }

        logging.info(f"Sending response {cmd}")
        self._chan.write(json.dumps(cmd).encode('utf-8'))


class KorvServer(asyncssh.SSHServer):
    VERBS = ('GET', 'STORE', 'UPDATE', 'DELETE')

    _callbacks = { verb: dict() for verb in VERBS}

    def __init__(self, port=8022, host_keys=['ssh_host_key'], authorized_client_keys='authorized_keys'):
        """Instatiate an SSH server that listens on the given port for clients that match the authorized keys"""

        self.port = port
        self._host_keys = host_keys
        self._authorized_client_keys = authorized_client_keys

    def connection_requested(self, dest_host, dest_port, orig_host, orig_port):
        """Run a new TCP session that handles an SSH client connection"""

        logging.info("Connection requested", dest_host, dest_port, orig_host, orig_port)
        return _KorvServerSession(KorvServer._callbacks)

    async def __create_server(self):
        """Creates an asynchronous SSH server"""

        await asyncssh.create_server(
            KorvServer, '', self.port,
            server_host_keys=self._host_keys,
            authorized_client_keys=self._authorized_client_keys
        )

    def add_callback(self, verb, resource, callback):
        """Configure a callable to execute when receiving a request with the given verb and resource combination"""

        if verb not in KorvServer.VERBS:
            raise ValueError(f"Verb must be one of {KorvServer.VERBS}")

        if resource not in KorvServer._callbacks[verb]:
            KorvServer._callbacks[verb][resource] = list()

        KorvServer._callbacks[verb][resource].append(callback)

    def start(self):
        """Start the server"""

        logging.info(f"Listening on port {self.port}")

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self.__create_server())
        except (OSError, asyncssh.Error) as exc:
            sys.exit(f'Error starting server: {exc}')

        loop.run_forever()

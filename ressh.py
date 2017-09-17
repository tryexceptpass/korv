import asyncio
import asyncssh

import sys
import traceback
import time
import json


class ReSSHServerSession(asyncssh.SSHTCPSession):
    def __init__(self, callbacks):
        self._callbacks = callbacks

    def connection_made(self, chan):
        print("Connection incoming")
        self._chan = chan

    def connection_lost(self, exc):
        print("Connection lost")
        print(str(exc))

    def session_started(self):
        print("Connection successful")
        # self._chan.write('Hi'.encode('utf8'))

    def data_received(self, data, datatype):
        print(f"Received data: {data}")

        self._dispatch(data)

    def eof_received(self):
        # self._chan.write('Total = %s\n' % self._total)
        print("EOF")
        self._chan.exit(0)

    def _dispatch(self, data):
        try:
            request = json.loads(data.decode('utf-8'))
            if 'id' not in request:
                print("Malformed request: missing 'id'")
                self._send_response(0, 400, {"message": "Missing 'id'"})

            if 'verb' not in request:
                print("Malformed request: missing 'request'")
                self._send_response(request['id'], 400, {"message": "Missing 'verb'"})

            if 'resource' not in request:
                print("Malformed request: missing 'resource'")
                self._send_response(request['id'], 400, {"message": "Missing 'resource'"})

            if request['verb'] == 'STORE' and 'body' not in request['request']:
                print("Malformed request: missing 'resource'")
                self._send_response(request['id'], 400, {"message": "Missing 'body'"})

            elif request['verb'] == 'UPDATE' and 'body' not in request['request']:
                print("Malformed request: missing 'resource'")
                self._send_response(request['id'], 400, {"message": "Missing 'body'"})

        except Exception as e:
            print("Unable to process request")
            self._send_response(0, 400, {"message": "Unable to process request"})

        self._process_request(request)

    def _process_request(self, request):
        if request['verb'] not in self._callbacks:
            print(f"No callback found for {request['verb']}")
            self._send_response(request['id'], 404)
            return

        if request['resource'] not in self._callbacks[request['verb']]:
            print(f"No callback found for {request['verb']} on {request['resource']}")
            self._send_response(request['id'], 404)
            return

        for callback in self._callbacks[request['verb']][request['resource']]:
            try:
                self._send_response(request['id'], *callback(request))

            except Exception as e:
                print(f"Internal error when executing {request['verb']} on {request['resource']}")
                self._send_response(request['id'], 500, {"message": str(e), "traceback": traceback.format_exc()})

    def _send_response(self, request_id, code, body=None):
        cmd = {
            'id': time.time(),
            'request_id': request_id,
            'code': code,
            'body': body
        }

        print(f"Sending response {cmd}")
        self._chan.write(json.dumps(cmd).encode('utf-8'))


class ReSSHServer(asyncssh.SSHServer):
    _callbacks = {
        'GET': dict(),
        'STORE': dict(),
        'UPDATE': dict(),
        'DELETE': dict()
    }

    def __init__(self, port=8022):
        self.port = 8022

    def connection_requested(self, dest_host, dest_port, orig_host, orig_port):
        print("Connection requested", dest_host, dest_port, orig_host, orig_port)
        # return asyncssh.create_tcp_channel(), MySSHServerSession()
        return ReSSHServerSession(ReSSHServer._callbacks)

    async def _create_server(self):
        await asyncssh.create_server(ReSSHServer, '', self.port,
                                     server_host_keys=['ssh_host_key'],
                                     authorized_client_keys='ssh_authorized_keys')

    def add_callback(self, verb, resource, callback):
        if resource not in ReSSHServer._callbacks[verb]:
            ReSSHServer._callbacks[verb][resource] = list()

        ReSSHServer._callbacks[verb][resource].append(callback)

    def start(self):
        print(f"Listening on port {self.port}")

        loop = asyncio.get_event_loop()

        try:
            loop.run_until_complete(self._create_server())
        except (OSError, asyncssh.Error) as exc:
            sys.exit('Error starting server: ' + str(exc))

        loop.run_forever()

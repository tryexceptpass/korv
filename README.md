Korv is an API framework that uses TCP sockets over SSH to exchange JSON data with a REST-like protocol. It's built on top of the `asyncssh` module, so it uses `asyncio` to manage the sockets and its callbacks. This allows you to build rich APIs with the session security of SSH and without the TCP overhead of HTTP.

Communications over this framework requires SSH keys like logging into a normal SSH server:
* The server itself has a private key and a set of public keys for the authorized clients.
* The client has a private key and a set of public keys for the servers it can connect to.


## Verbs
There are 4 main verbs that indicate the intent of your request:
* `GET` for retrieving information.
* `STORE` for creating new objects.
* `UPDATE` for changing existing objects.
* `DELETE` for removing objects.


## Keys
As discussed previously, you establish an SSH session with the server, so it's possible to reuse existing keys or generate them through any standard mechanism like the one below:

```bash
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
```

## Server
Getting a server up and running is very simple:

```python
from korv import KorvServer


def hello(request):
    """Callback for the /hello endpoint"""

    return 200, {'msg': 'Hello World!'}

def echo(request):
    """Callback for the /echo endpoint"""

    return 200, {'msg': f'{request}'}


# Create a server
k = KorvServer(host_keys=['PATH_TO_YOUR_SERVER_PRIVATE_KEY'], authorized_client_keys='PATH_TO_YOUR_AUTHORIZED_PUBLIC_KEYS')

# Register the callbacks
k.add_callback('GET', '/hello', hello)
k.add_callback('GET', '/echo', echo)

# Start listening for requests
k.start()
```

This will start a new SSH server with the specified private key that listens on port `8022` by default and will accept the clients listed in the authorized keys.

## Client
Following is an example on how to communicate with this server.

```python
>>> from korv import KorvClient
>>>
>>> # Create the client
>>> k = KorvClient(client_keys=['PATH_TO_YOUR_CLIENTS_PRIVATE_KEY'])
>>>
>>> # Issue a GET request and print the output
>>> k.get('/hello', callback=lambda response: print(response['body']))
>>> {'msg': 'Hello World!'}
```

## Return Codes
We're using standard HTTP response codes:
* `200` = Success.
* `400` = Malformed request or missing parameters.
* `404` = NotFound
* `500` = Internal error.

Server exceptions map to a `500` return code ans will include a traceback in the response.

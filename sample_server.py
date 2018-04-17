import logging

from korv import KorvServer


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(asctime)s %(message)s')

def callme(request):
    return 200, {'msg': 'Hello World!'}

def echo(request):
    return 200, {'msg': f'{request}'}

k = KorvServer()
k.add_callback('GET', '/hello', callme)
k.add_callback('GET', '/echo', echo)
k.start()

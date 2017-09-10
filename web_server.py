import os

from common import create_folders, decode, encode, decode_dict_strings, create_file
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints
from shutil import rmtree


class Service(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('root_folder', self)
        self.putChild('folders', self)
        self.putChild('file', self)
        self.root_folder_name = ''

    def render_GET(self, request):
        uri = decode(request.uri)
        endpoint = uri.split('?')[0]
        uri_params = decode_dict_strings(request.args)
        print('endpoint: {}\nparams: {}\n'.format(endpoint, uri_params))
        self.handle_request(endpoint, uri_params)
        return encode('OK')

    def render_POST(self, request):
        uri = decode(request.uri)
        endpoint = uri.split('?')[0]
        file_body = request.content.read()
        uri_params = decode_dict_strings(request.args)
        print('endpoint: {}\nparams: {}\n'.format(endpoint, uri_params))
        create_file(uri_params['path'][0], file_body)
        return encode('server response: endpoint - {}, status - OK'.format(endpoint))

    def handle_request(self, endpoint, params):
        if endpoint == '/root_folder':
            self.root_folder_name = params['root'][0]
            create_folders(self.root_folder_name)
            folders = params['folders']
            create_folders(folders)
        elif endpoint == '/folders':
            for folder in params.get('removed', []):
                if os.path.exists(folder):
                    rmtree(folder)
            for folder in params.get('added', []):
                os.makedirs(folder, exist_ok=True)
        elif endpoint == '/end_of_session':
            rmtree(self.root_folder_name)

    def __del__(self):
        rmtree(self.root_folder_name)


class Runner(Resource):
    def getChild(self, name, request):
        return Service()


def main():
    working_directory = 'server_directory'  # TODO: remove
    if not os.path.exists(working_directory):
        os.makedirs(working_directory, exist_ok=True)
    os.chdir(working_directory)
    service = Runner()
    factory = Site(service)
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
    endpoint.listen(factory)
    reactor.run()

if __name__ == '__main__':
    main()

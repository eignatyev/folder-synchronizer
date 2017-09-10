import json
import os

import _thread
from time import sleep

from common import create_folder, decode, encode, decode_dict_strings, create_file, remove_file, move_file, \
    remove_folder
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints


class Service(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('root_folder', self)
        self.putChild('root_data', self)
        self.putChild('file', self)
        self.root_folder_name = None

        self.files_to_create_queue = []
        _thread.start_new_thread(self.create_files_from_queue, ())

    def render_GET(self, request):
        uri = decode(request.uri)
        endpoint = uri.split('?')[0]
        uri_params = decode_dict_strings(request.args)
        print('endpoint: {}\nparams: {}\n'.format(endpoint, uri_params))
        return self.handle_get_request(endpoint, uri_params)

    def handle_get_request(self, endpoint, params):
        files_to_request = []

        if endpoint == '/root_folder':
            self.root_folder_name = params['name'][0]
            create_folder(self.root_folder_name)
            return encode('Root folder "{}" created'.format(self.root_folder_name))

        elif endpoint == '/root_data':
            for folder in params.get('folders', []):  # creating folders
                create_folder(folder)
            for file_path in params.get('files', []):  # requesting unexistent files
                if not os.path.exists(file_path):
                    files_to_request.append(file_path)
            return encode(json.dumps(dict(post_files=files_to_request)))

        elif endpoint == '/diff':
            for folder_path in params.get('removed_folders', []):
                remove_folder(folder_path)
            for folder_path in params.get('added_folders', []):
                create_folder(folder_path)
            for file_path in params.get('removed_files', []):
                remove_file(file_path)
            for paths in params.get('moved_files', []):
                paths = json.loads(paths)
                move_file(paths['from'], paths['to'])
            for file_path in params.get('added_files', []):
                files_to_request.append(file_path)
            return encode(json.dumps(dict(post_files=files_to_request)))

        elif endpoint == '/end_of_session':
            remove_folder(self.root_folder_name)

    def render_POST(self, request):
        uri = decode(request.uri)
        endpoint = uri.split('?')[0]
        body = request.content.read()
        uri_params = decode_dict_strings(request.args) if request.args else {}
        print('endpoint: {}\nparams: {}\n'.format(endpoint, uri_params))
        return self.handle_post_request(endpoint, uri_params, body)

    def handle_post_request(self, endpoint, params, body):
        files_to_request = []

        if endpoint == '/file':
            self.files_to_create_queue.append(dict(path=params['path'][0], body=body))
            return encode('server response: endpoint - {}, status - OK'.format(endpoint))

        elif endpoint == '/root_data':
            body_dict = json.loads(body)
            for folder in body_dict.get('folders', []):  # creating folders
                create_folder(folder)
            for file_path in body_dict.get('files', []):  # requesting unexistent files
                if not os.path.exists(file_path):
                    files_to_request.append(file_path)
            return encode(json.dumps(dict(post_files=files_to_request)))

    def create_files_from_queue(self):
        while self:
            if self.files_to_create_queue:
                file_data = self.files_to_create_queue.pop(0)
                create_file(file_data['path'], file_data['body'])
            else:
                sleep(1)  # if no files in queue - check once per second

    def __del__(self):
        remove_folder(self.root_folder_name)


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

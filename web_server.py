import _thread

from common import *
from time import sleep
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor, endpoints


class Server(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild('root_folder', self)
        self.putChild('root_data', self)
        self.putChild('file', self)
        self.putChild('end_of_session', self)

        self.files_to_create_queue = []
        _thread.start_new_thread(self.create_files_from_queue, ())

    def render_GET(self, request):
        uri = decode(request.uri)
        endpoint = uri.split('?')[0]
        uri_params = decode_dict_strings(request.args)
        print('\nendpoint: {}\nparams: {}\n'.format(endpoint, uri_params))
        return self.handle_get_request(endpoint, uri_params)

    @staticmethod
    def handle_get_request(endpoint, params):
        files_to_request = []

        if endpoint == '/diff':
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
            root_folder_name = params.get('remove_folder', [])[0]
            remove_folder(root_folder_name)
            return encode('session dropped, root folder "{}" removed'.format(root_folder_name))

    def render_POST(self, request):
        uri = decode(request.uri)
        endpoint = uri.split('?')[0]
        body = request.content.read()
        uri_params = decode_dict_strings(request.args) if request.args else {}
        print('\nendpoint: {}\nparams: {}\n'.format(endpoint, uri_params))
        return self.handle_post_request(endpoint, uri_params, body)

    def handle_post_request(self, endpoint, params, body):
        files_to_request = []

        if endpoint == '/file':
            file_path = params['path'][0]
            self.files_to_create_queue.append(dict(path=file_path, body=body))
            return encode('file "{}" - OK'.format(file_path))

        elif endpoint == '/root_data':
            body_dict = json.loads(body)
            for folder in body_dict.get('folders', []):  # creating folders
                create_folder(folder)
                print('created "{}" folder'.format(folder))
            for file_path in body_dict.get('files', []):  # requesting unexistent files
                if not os.path.exists(file_path):
                    files_to_request.append(file_path)
                    print('requested "{}" file'.format(file_path))
            return encode(json.dumps(dict(post_files=files_to_request)))

    def create_files_from_queue(self):
        while self:
            if self.files_to_create_queue:
                file_data = self.files_to_create_queue.pop(0)
                create_file(file_data['path'], file_data['body'])
            else:
                sleep(1)  # if no files in queue - check once per second


class Runner(Resource):
    def getChild(self, name, request):
        return Server()


def stop_server():
    input('\n\nPress ENTER to stop the server!\n\n')
    reactor.stop()


def main():
    service = Runner()
    factory = Site(service)
    endpoint = endpoints.TCP4ServerEndpoint(reactor, 8880)
    endpoint.listen(factory)
    _thread.start_new_thread(stop_server, ())
    reactor.run()

if __name__ == '__main__':
    main()

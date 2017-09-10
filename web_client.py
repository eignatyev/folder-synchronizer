import json
import os
import sys
import treq

from common import FolderChecker, read_file, encode
from twisted.internet import task, reactor
from twisted.internet.defer import inlineCallbacks, Deferred


class Client:
    working_directory = 'client_directory'  # TODO: remove
    if not os.path.exists(working_directory):
        os.makedirs(working_directory, exist_ok=True)
    host_address = 'http://127.0.0.1:8880'

    def __init__(self, root_folder_name):
        os.chdir(self.working_directory)
        self.root_folder_name = root_folder_name
        self.folder_checker = FolderChecker(web_client=self)
        self.send_initial_root_data()
        self.current_diff = None  # Last tracked files and folders changes

        # repeating = task.LoopingCall(self.exchange_folder_data_with_server)
        # repeating.start(3)

    def send_initial_root_data(self):
        self.send_root_folder_name()
        self.exchange_root_data_with_server()

    @inlineCallbacks
    def exchange_root_data_with_server(self):
        root_data_response = yield self.send_request(
            method='POST',
            endpoint='/root_data',
            data=encode(json.dumps(dict(
                folders=self.folder_checker.saved_folders,
                files=self.folder_checker.saved_files_data
            )))
        )
        print(1)
        self.send_files(root_data_response)

    @inlineCallbacks
    def send_file(self, file_path):
        files_response = yield self.send_request(
            method='POST',
            endpoint='/file',
            params={'path': file_path},
            data=read_file(file_path)
        )
        print(files_response)

    def send_files(self, raw_response):
        root_data_dict = json.loads(raw_response)
        for file_ in root_data_dict.get('post_files', []):
            self.send_file(file_)

    @inlineCallbacks
    def send_root_folder_name(self):
        root_response = yield self.send_request(
            method='GET',
            endpoint='/root_folder',
            params={'name': self.root_folder_name}
        )
        print(root_response)
        return root_response

    @inlineCallbacks
    def send_diff_data(self, diff):
        diff_response = yield self.send_request(
            method='GET',
            endpoint='/diff',
            params=diff
        )
        self.send_files(diff_response)

    @inlineCallbacks
    def send_request(self, method, endpoint, params=None, data=None):
        if method.lower() == 'get':
            response = yield treq.get(self.host_address + endpoint, headers=None, params=params)
            content = yield response.text()
        elif method.lower() == 'post':
            response = yield treq.post(self.host_address + endpoint, params=params, data=data)
            content = yield response.text()
        else:
            raise IndexError('Wrong http method')
        return content

    @inlineCallbacks
    def __del__(self):
        response = yield self.send_request(method='GET', endpoint='/end_of_session')
        print(response)


def main():
    if len(sys.argv) == 2:
        root_folder_name = sys.argv[-1]
        _ = Client(root_folder_name)
        reactor.run()
    else:
        print('Program usage example: python3 web_client.py <folder_path>')
        exit()

if __name__ == '__main__':
    main()

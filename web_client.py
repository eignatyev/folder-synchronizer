import os
import sys
import treq

from common import FolderChecker, read_file
from twisted.internet import task, reactor
from twisted.internet.defer import inlineCallbacks


class Client:
    working_directory = 'client_directory'  # TODO: remove
    if not os.path.exists(working_directory):
        os.makedirs(working_directory)
    host_address = 'http://127.0.0.1:8880'

    def __init__(self, root_folder_name):
        os.chdir(self.working_directory)
        self.root_folder_name = root_folder_name
        self.folder_checker = FolderChecker(web_client=self)
        self.send_initial_root_data()

        repeating = task.LoopingCall(self.exchange_folder_data_with_server)
        repeating.start(60)

    def exchange_folder_data_with_server(self):
        url = self.host_address + '/root_folder'
        d = treq.get(url)
        d.addCallback(treq.content)
        return d

    @inlineCallbacks
    def send_initial_root_data(self):
        folders, file_paths = self.folder_checker.get_root_data()
        folders_response = yield self.send_request(
            method='GET',
            endpoint='/root_folder',
            params={'root': self.root_folder_name, 'folders': folders}
        )
        print(folders_response)
        for file_path in file_paths:
            files_response = yield self.send_request(
                method='POST',
                endpoint='/file',
                params={'path': file_path},
                data=read_file(file_path)
            )
            print(files_response)

    @inlineCallbacks
    def send_request(self, method, endpoint, params=None, data=None):
        if method.lower() == 'get':
            response = yield treq.get(self.host_address + endpoint, headers=None, params=params)
            content = yield response.text()
        elif method.lower() == 'post':
            response = yield treq.post(self.host_address + endpoint, params=params, data=data)
            content = yield response.text()
        else:
            raise IndexError('Wrong method')
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

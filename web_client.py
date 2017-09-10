import sys

import _thread
from time import sleep

import treq

from common import *
from twisted.internet import task, reactor
from twisted.internet.defer import inlineCallbacks


class Client:
    host_address = 'http://127.0.0.1:8880'

    def __init__(self, root_folder):
        self.root_folder_path, self.root_folder_name = os.path.split(root_folder)
        os.chdir(self.root_folder_path)
        self.folder_checker = FolderChecker(web_client=self)
        self.send_initial_root_data()

        self.files_to_send_queue = []
        _thread.start_new_thread(self.send_files_from_queue, ())
        _thread.start_new_thread(self.stop_session, ())

        # self.current_diff = None  # Last tracked files and folders changes
        # repeating = task.LoopingCall(self.exchange_folder_data_with_server)
        # repeating.start(3)

    def send_initial_root_data(self):
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
        requested_files = json.loads(root_data_response)['post_files']
        self.files_to_send_queue += requested_files

    @inlineCallbacks
    def send_file(self, file_path):
        files_response = yield self.send_request(
            method='POST',
            endpoint='/file',
            params={'path': file_path},
            data=read_file(file_path)
        )
        print('sent "{}" file'.format(file_path))
        self.print_server_response(files_response)

    def send_files(self, raw_response):
        root_data_dict = json.loads(raw_response)
        for file_ in root_data_dict.get('post_files', []):
            self.send_file(file_)

    @inlineCallbacks
    def send_root_folder_name(self):
        root_response = yield self.send_request(
            method='GET',
            endpoint='/root_folder',
            params={'name': os.path.split(self.root_folder_name)[-1]}
        )
        self.print_server_response(root_response)
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
        if params is None:
            params = {}
        if method.lower() == 'get':
            response = yield treq.get(self.host_address + endpoint, headers=None, params=params)
            content = yield response.text()
        elif method.lower() == 'post':
            response = yield treq.post(self.host_address + endpoint, params=params, data=data)
            content = yield response.text()
        else:
            raise IndexError('Wrong http method')
        return content

    @staticmethod
    def print_server_response(response):
        print('SERVER RESPONSE: {}'.format(response))

    @inlineCallbacks
    def send_end_of_session_command(self):
        response = yield self.send_request(
            method='GET',
            endpoint='/end_of_session',
            params=dict(remove_folder=self.root_folder_name)
        )
        self.print_server_response(response)

    @inlineCallbacks
    def stop_session(self):
        input('\n\nPress ENTER to stop the session!\n\n')
        yield self.send_end_of_session_command()
        reactor.stop()

    def send_files_from_queue(self):
        while self:
            if self.files_to_send_queue:
                file_path = self.files_to_send_queue.pop(0)
                self.send_file(file_path)
            else:
                sleep(1)  # if no files in queue - check once per second


def main():
    if len(sys.argv) == 2:
        root_folder_name = sys.argv[-1]
        Client(root_folder_name)
        reactor.run()
    else:
        print('Program usage example: python3 web_client.py <folder_path>')
        exit()

if __name__ == '__main__':
    main()

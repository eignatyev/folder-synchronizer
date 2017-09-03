import _thread
import hashlib
import os
import time


class FolderChecker:
    def __init__(self, web_client=None):
        self.folder_name = web_client.root_folder_name
        self.current_folders, self.current_files = self.get_root_data()
        _thread.start_new_thread(self.check_folder_state, ())

    def get_root_data(self):
        """
        Returns a tuple of two lists: absolute folders paths and absolute files paths
        :return: ([folders_paths], [files_paths])
        """
        folders_data = [[folders, files] for folders, _, files in os.walk(self.folder_name)]
        folders = []
        files = []
        for folder_data in folders_data:
            folder_name_ = folder_data[0]
            folder_files = folder_data[1]
            folders.append(folder_name_)
            for f in folder_files:
                files.append(os.path.join(folder_name_, f))
        return folders, files

    def get_folders_diff(self, folders):
        """
        Compares saved folders list with the current one
        :param folders: list
        :return: ([missing_folders], [added_folders])
        """
        missing_folders = list(set(self.current_folders).difference(set(folders)))
        added_folders = list(set(folders).difference(set(self.current_folders)))
        if any([missing_folders, added_folders]):
            self.current_folders = folders
        return missing_folders, added_folders

    def get_files_diff(self, folders):
        # TODO
        pass

    def get_diff(self):
        """
        Returns a dictionary with changed, new and missing files/folders
        :return: dict(...)
        """
        folders, files = self.get_root_data()
        missing_folders, added_folders = self.get_folders_diff(folders)
        return dict(missing_folders=missing_folders, added_folders=added_folders)

    def check_folder_state(self):
        """
        Infinite checker to determine any changes with files and folders
        """
        while self:
            diff = self.get_diff()
            if diff['missing_folders']:
                pass
            if diff['added_folders']:
                pass
            time.sleep(1)


def read_bytes_from_file(file_path, chunk_size=8100):
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if chunk:
                yield chunk
            else:
                break


def read_file(file_path):
    with open(file_path, 'rb') as file_:
        return file_.read()


def create_folders(folders):
    if isinstance(folders, str):
        folders = folders.split(',')
    for f in folders:
        if not os.path.exists(f):
            os.makedirs(f)


def create_file(file_path, body):
    with open(file_path, 'wb') as f:
        f.write(bytearray(body))


def decode(s):
    return s.decode('utf-8')


def encode(s):
    return bytes(s, encoding='utf-8')


def deep_decode(container):
    if isinstance(container, list):
        return list(map(decode, container))
    elif isinstance(container, bytes):
        return decode(container)


def decode_dict_strings(params):
    return {decode(k): deep_decode(v) for k, v in params.items()}


def get_file_md5_hash(file_path):
    with open(file_path, 'rb') as file_:
        return hashlib.md5(file_.read()).hexdigest()

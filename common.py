import _thread
import hashlib
import json
import os
import shutil
import time


class FolderChecker:
    """
    Purpose - track, collect root folder data and calculate certain data diffs
    Potentially can be used by both, a server and a client
    """
    def __init__(self, web_client=None, web_server=None):
        self.parent = web_client or web_server
        self.parent_class_name = self.parent.__class__.__name__
        if self.parent_class_name == 'Client':
            self.folder_name = self.parent.root_folder_name
            self.saved_folders, self.saved_files_data = self.get_root_data()
            _thread.start_new_thread(self.check_folder_state, ())
        elif self.parent_class_name == 'Server':  # server does not have such data initially
            self.folder_name = None
            self.saved_folders, self.saved_files_data = None, None

    def get_root_data(self):
        """
        Returns a tuple of two lists: absolute folders paths and absolute files paths
        :return: ([folders_paths], {<files_data>file_path: file_hash})
        """
        folders_data = [[folders, files] for folders, _, files in os.walk(self.folder_name)]
        folders = []
        files_data = {}
        for folder_data in folders_data:
            folder_name_ = folder_data[0]
            folder_files = folder_data[1]
            folders.append(folder_name_)
            for f in folder_files:
                file_abs_path = os.path.join('.', folder_name_, f)
                file_hash_sum = get_file_md5_hash(file_abs_path)
                if file_hash_sum:
                    files_data[file_abs_path] = file_hash_sum  # dict is useful here for access without looping
        return folders, files_data

    def get_folders_diff(self, folders):
        """
        Compares saved folders list with the current one
        :param folders: list
        :return: ([missing_folders], [added_folders])
        """
        missing_folders = list(set(self.saved_folders).difference(set(folders)))
        added_folders = list(set(folders).difference(set(self.saved_folders)))
        if any([missing_folders, added_folders]):
            self.saved_folders = folders
        return missing_folders, added_folders

    def get_files_diff(self, current_files_data):
        """
        Compares saved files data with the current files data
        :param current_files_data: list of dicts
        :return: ([<missing_files_paths>str], [<added_files_paths>str], [<moved_files_paths>{'from': str, 'to': str}])
        """
        if self.saved_files_data:
            saved_files_paths, saved_files_hashes = zip(*self.saved_files_data.items())
        else:
            saved_files_paths, saved_files_hashes = [], []
        if current_files_data:
            current_files_paths, current_files_hashes = zip(*current_files_data.items())
        else:
            current_files_paths, current_files_hashes = [], []

        missing_files_paths = list(set(saved_files_paths).difference(set(current_files_paths)))
        missing_files_hashes = [self.saved_files_data[path] for path in missing_files_paths]
        added_files_paths = list(set(current_files_paths).difference(set(saved_files_paths)))
        added_files_hashes = [current_files_data[path] for path in added_files_paths]

        # get moved files paths
        moved_files_hashes = list(set(missing_files_hashes).intersection(set(added_files_hashes)))
        moved_files_paths = [
            json.dumps({
                'from': self.get_file_path_by_hash(self.saved_files_data, hash_),
                'to': self.get_file_path_by_hash(current_files_data, hash_)
            }) for hash_ in moved_files_hashes
        ]

        # get missing files paths
        missing_files_paths = [  # remove "moved" files paths
            self.get_file_path_by_hash(self.saved_files_data, hash_)
            for hash_ in missing_files_hashes if hash_ not in moved_files_hashes
        ]

        # get added files paths
        added_files_paths = [  # remove "moved" files paths
            self.get_file_path_by_hash(current_files_data, hash_)
            for hash_ in added_files_hashes if hash_ not in moved_files_hashes
        ]

        # get edited files paths
        remained_files_paths = list(set(saved_files_paths).intersection(set(current_files_paths)))
        for file_path in remained_files_paths:
            if self.saved_files_data[file_path] != current_files_data[file_path]:  # compare hashes
                missing_files_paths.append(file_path)
                added_files_paths.append(file_path)

        if any([missing_files_paths, added_files_paths, moved_files_paths]):
            self.saved_files_data = current_files_data

        return missing_files_paths, added_files_paths, moved_files_paths

    @staticmethod
    def get_file_path_by_hash(files_data, hash_):
        for file_path, file_hash in files_data.items():
            if file_hash == hash_:
                return file_path
        return None

    def get_diff(self):
        """
        Returns a dictionary with changed, new and missing files/folders
        :return: dict(...)
        """
        folders, files_data = self.get_root_data()
        missing_files, added_files, moved_files = self.get_files_diff(files_data)
        missing_folders, added_folders = self.get_folders_diff(folders)
        if any([missing_folders, added_folders, missing_files, added_files, moved_files]):
            return dict(
                removed_folders=missing_folders,
                added_folders=added_folders,
                removed_files=missing_files,
                added_files=added_files,
                moved_files=moved_files
            )
        return None

    def check_folder_state(self):
        """
        Infinite checker to determine any files and folders changes
        """
        while self:
            diff = self.get_diff()
            print(diff or 'No changes detected')
            if diff:
                self.parent.send_diff_data(diff)
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


def create_folder(folder):
        os.makedirs(folder, exist_ok=True)


def remove_folder(folder_path):
    shutil.rmtree(folder_path, ignore_errors=True)


def create_file(file_path, body):
    try:
        with open(file_path, 'wb') as f:
            f.write(bytearray(body))
    except Exception as e:
        print(e)


def remove_file(file_path):
    os.remove(file_path)


def move_file(from_, to_):
    os.rename(from_, to_)


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
    if os.path.exists(file_path):  # avoid working with removed files
        modification_time = str(os.path.getmtime(file_path) * (10 ** 7))  # remove floating point
        binary_modification_time = encode(modification_time)
        with open(file_path, 'rb') as file_:
            return hashlib.md5(binary_modification_time + file_.read()).hexdigest()
    return None


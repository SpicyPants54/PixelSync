import hashlib


def calculate_hash(file_path):

    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:

        while chunk := file.read(1024 * 1024):

            sha256.update(chunk)

    return sha256.hexdigest()
   
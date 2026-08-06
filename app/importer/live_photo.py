from pathlib import Path


def find_pair(file, folder):

    file = Path(file)

    for item in Path(folder).iterdir():

        if item.stem == file.stem:

            if item.suffix.lower() != file.suffix.lower():

                return item

    return None
from pathlib import Path

from app.importer.media_bundle import MediaBundle


def build_bundle(file, folder):

    file = Path(file)

    bundle = [
        file
    ]


    for item in Path(folder).iterdir():

        if item.stem == file.stem:

            if item != file:

                bundle.append(
                    item
                )


    return MediaBundle(
        bundle
    )
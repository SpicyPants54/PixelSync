from pathlib import Path


IMAGE_TYPES = {
    ".jpg",
    ".jpeg",
    ".heic",
    ".png"
}


VIDEO_TYPES = {
    ".mov",
    ".mp4"
}


def get_media_group(file):

    file = Path(file)

    stem = file.stem

    group = {
        "image": None,
        "video": None
    }


    if file.suffix.lower() in IMAGE_TYPES:

        group["image"] = file


    elif file.suffix.lower() in VIDEO_TYPES:

        group["video"] = file


    return group
import ctypes
import os
from pathlib import Path, PurePosixPath

from loguru import logger


AFC_FOPEN_RDONLY = 1


class IPhoneAFCError(RuntimeError):
    pass


class IPhoneAFC:

    def __init__(
        self,
        tool_directory,
        udid,
        transport="usb"
    ):

        if transport not in {
            "usb",
            "wifi",
        }:

            raise ValueError(
                "transport must be usb or wifi"
            )

        self.tool_directory = Path(
            tool_directory
        )

        self.udid = udid
        self.transport = transport

        self.library = None
        self.device = ctypes.c_void_p()
        self.client = ctypes.c_void_p()
        self.dll_directory = None


    def _check(
        self,
        result,
        operation
    ):

        if result != 0:

            raise IPhoneAFCError(
                f"{operation} failed "
                f"with error {result}"
            )


    def _configure_library(self):

        library_path = (
            self.tool_directory
            /
            "libimobiledevice-1.0.dll"
        )

        if not library_path.is_file():

            raise IPhoneAFCError(
                f"Missing libimobiledevice library: "
                f"{library_path}"
            )

        if (
            os.name == "nt"
            and
            hasattr(
                os,
                "add_dll_directory"
            )
        ):

            self.dll_directory = (
                os.add_dll_directory(
                    str(self.tool_directory)
                )
            )

        self.library = ctypes.CDLL(
            str(library_path)
        )

        self.library.idevice_new_with_options.argtypes = [
            ctypes.POINTER(
                ctypes.c_void_p
            ),
            ctypes.c_char_p,
            ctypes.c_int,
        ]

        self.library.idevice_new_with_options.restype = (
            ctypes.c_int
        )

        self.library.idevice_free.argtypes = [
            ctypes.c_void_p,
        ]

        self.library.idevice_free.restype = (
            ctypes.c_int
        )

        self.library.afc_client_start_service.argtypes = [
            ctypes.c_void_p,
            ctypes.POINTER(
                ctypes.c_void_p
            ),
            ctypes.c_char_p,
        ]

        self.library.afc_client_start_service.restype = (
            ctypes.c_int
        )

        self.library.afc_client_free.argtypes = [
            ctypes.c_void_p,
        ]

        self.library.afc_client_free.restype = (
            ctypes.c_int
        )

        self.library.afc_read_directory.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.POINTER(
                ctypes.POINTER(
                    ctypes.c_char_p
                )
            ),
        ]

        self.library.afc_read_directory.restype = (
            ctypes.c_int
        )

        self.library.afc_get_file_info.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.POINTER(
                ctypes.POINTER(
                    ctypes.c_char_p
                )
            ),
        ]

        self.library.afc_get_file_info.restype = (
            ctypes.c_int
        )

        self.library.afc_dictionary_free.argtypes = [
            ctypes.POINTER(
                ctypes.c_char_p
            ),
        ]

        self.library.afc_dictionary_free.restype = (
            ctypes.c_int
        )

        self.library.afc_file_open.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_uint64,
            ctypes.POINTER(
                ctypes.c_uint64
            ),
        ]

        self.library.afc_file_open.restype = (
            ctypes.c_int
        )

        self.library.afc_file_read.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(
                ctypes.c_uint32
            ),
        ]

        self.library.afc_file_read.restype = (
            ctypes.c_int
        )

        self.library.afc_file_close.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint64,
        ]

        self.library.afc_file_close.restype = (
            ctypes.c_int
        )


    def connect(self):

        if self.client.value:

            return

        self._configure_library()

        lookup_options = (
            2
            if self.transport == "wifi"
            else 1
        )

        self._check(
            self.library.idevice_new_with_options(
                ctypes.byref(
                    self.device
                ),
                self.udid.encode(
                    "utf-8"
                ),
                lookup_options
            ),
            "Connecting to iPhone"
        )

        try:

            self._check(
                self.library.afc_client_start_service(
                    self.device,
                    ctypes.byref(
                        self.client
                    ),
                    b"PixelSync"
                ),
                "Starting AFC service"
            )

        except Exception:

            self.close()
            raise


    def close(self):

        if self.library and self.client.value:

            self.library.afc_client_free(
                self.client
            )

            self.client = ctypes.c_void_p()

        if self.library and self.device.value:

            self.library.idevice_free(
                self.device
            )

            self.device = ctypes.c_void_p()

        if self.dll_directory:

            self.dll_directory.close()
            self.dll_directory = None


    def __enter__(self):

        self.connect()

        return self


    def __exit__(
        self,
        exception_type,
        exception,
        traceback
    ):

        self.close()


    def _read_dictionary(
        self,
        values
    ):

        result = {}
        index = 0

        while values[index]:

            key = values[index].decode(
                "utf-8"
            )

            value = values[index + 1]

            if value is None:

                break

            result[key] = value.decode(
                "utf-8"
            )

            index += 2

        return result


    def list_directory(
        self,
        remote_path
    ):

        entries = ctypes.POINTER(
            ctypes.c_char_p
        )()

        self._check(
            self.library.afc_read_directory(
                self.client,
                str(remote_path).encode(
                    "utf-8"
                ),
                ctypes.byref(
                    entries
                )
            ),
            f"Listing {remote_path}"
        )

        try:

            result = []
            index = 0

            while entries[index]:

                name = entries[index].decode(
                    "utf-8"
                )

                if name not in {
                    ".",
                    "..",
                }:

                    result.append(
                        name
                    )

                index += 1

            return result

        finally:

            self.library.afc_dictionary_free(
                entries
            )


    def get_file_info(
        self,
        remote_path
    ):

        values = ctypes.POINTER(
            ctypes.c_char_p
        )()

        self._check(
            self.library.afc_get_file_info(
                self.client,
                str(remote_path).encode(
                    "utf-8"
                ),
                ctypes.byref(
                    values
                )
            ),
            f"Reading file information for "
            f"{remote_path}"
        )

        try:

            return self._read_dictionary(
                values
            )

        finally:

            self.library.afc_dictionary_free(
                values
            )


    def walk_media(
        self,
        remote_root="/DCIM",
        extensions=None
    ):

        extensions = {
            extension.lower()
            for extension in (
                extensions
                or {
                    ".jpg",
                    ".jpeg",
                    ".png",
                    ".heic",
                    ".mov",
                    ".mp4",
                }
            )
        }

        pending = [
            PurePosixPath(
                remote_root
            )
        ]

        while pending:

            directory = pending.pop()

            for name in self.list_directory(
                directory
            ):

                path = directory / name
                info = self.get_file_info(
                    path
                )

                if info.get(
                    "st_ifmt"
                ) == "S_IFDIR":

                    pending.append(
                        path
                    )

                elif path.suffix.lower() in extensions:

                    yield path, info


    def download(
        self,
        remote_path,
        local_path,
        chunk_size=1024 * 1024
    ):

        remote_path = PurePosixPath(
            remote_path
        )

        local_path = Path(
            local_path
        )

        local_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        temporary_path = local_path.with_name(
            f".{local_path.name}.part"
        )

        handle = ctypes.c_uint64()

        self._check(
            self.library.afc_file_open(
                self.client,
                str(remote_path).encode(
                    "utf-8"
                ),
                AFC_FOPEN_RDONLY,
                ctypes.byref(
                    handle
                )
            ),
            f"Opening {remote_path}"
        )

        try:

            with open(
                temporary_path,
                "wb"
            ) as output:

                buffer = ctypes.create_string_buffer(
                    chunk_size
                )

                while True:

                    bytes_read = ctypes.c_uint32()

                    self._check(
                        self.library.afc_file_read(
                            self.client,
                            handle,
                            buffer,
                            chunk_size,
                            ctypes.byref(
                                bytes_read
                            )
                        ),
                        f"Reading {remote_path}"
                    )

                    if not bytes_read.value:

                        break

                    output.write(
                        buffer.raw[
                            :bytes_read.value
                        ]
                    )

            os.replace(
                temporary_path,
                local_path
            )

            logger.info(
                f"Imported iPhone media: "
                f"{remote_path}"
            )

            return local_path

        except Exception:

            temporary_path.unlink(
                missing_ok=True
            )

            raise

        finally:

            self.library.afc_file_close(
                self.client,
                handle
            )

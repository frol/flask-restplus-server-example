"""
Invoke tasks helper functions
=============================
"""
import logging
import os


log = logging.getLogger(__name__) # pylint: disable=invalid-name


def download_file(
        url,
        local_filepath,
        chunk_size=1024*512,
        lock_timeout=10,
        http_timeout=None,
        session=None
):
    # pylint: disable=too-many-arguments
    """
    A helper function which can download a file from a specified ``url`` to a
    local file ``local_filepath`` in chunks and using a file lock to prevent
    a concurrent download of the same file.
    """
    # Avoid unnecessary dependencies when the function is not used.
    import lockfile
    import requests

    log.debug("Checking file existance in '%s'", local_filepath)
    lock = lockfile.LockFile(local_filepath)
    try:
        lock.acquire(timeout=lock_timeout)
    except lockfile.LockTimeout:
        log.info(
            "File '%s' is locked. Probably another instance is still downloading it.",
            local_filepath
        )
        raise
    try:
        if not os.path.exists(local_filepath):
            log.info("Downloading a file from '%s' to '%s'", url, local_filepath)
            if session is None:
                session = requests
            response = session.get(url, stream=True, timeout=http_timeout)
            if response.status_code != 200:
                log.error("Download '%s' is failed: %s", url, response)
                response.raise_for_status()
            with open(local_filepath, 'wb') as local_file:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    # filter out keep-alive new chunks
                    if chunk:
                        local_file.write(chunk)
        log.debug("File '%s' has been downloaded", local_filepath)
        return local_filepath
    finally:
        lock.release()

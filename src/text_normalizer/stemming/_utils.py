import os
import sys
import tempfile

import requests
from pymystem3.mystem import _get_tarball_url


def install(path):
    """
    Install mystem binary as :py:const:`~pymystem3.constants.MYSTEM_BIN`.
    Overwrite if already installed.
    """

    url = _get_tarball_url()

    print("Installing mystem to %s from %s" % (path, url), file=sys.stdout)

    if not os.path.isdir(path):
        os.makedirs(path)

    tmp_fd, tmp_path = tempfile.mkstemp()
    try:
        r = requests.get(url, stream=True)
        with os.fdopen(tmp_fd, 'wb') as fd:
            for chunk in r.iter_content(64 * 1024):
                fd.write(chunk)
            fd.flush()

        if url.endswith('.tar.gz'):
            import tarfile
            tar = tarfile.open(tmp_path)
            try:
                tar.extract('mystem', path)
            finally:
                tar.close()
        elif url.endswith('.zip'):
            import zipfile
            zip = zipfile.ZipFile(tmp_path)
            try:
                zip.extractall(path)
            finally:
                zip.close()
        else:
            raise NotImplementedError("Could not install mystem from %s" % url)
    finally:
        os.unlink(tmp_path)
import os
import time
import requests
from urllib.parse import urlparse, unquote
from tqdm import tqdm
from pathlib import Path
from pySmartDL import SmartDL  #pip install pySmartDL


def cprint(text, color='red'):
    colors = {
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'magenta': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m'
    }
    if color not in colors:
        raise ValueError(f"Invalid color '{color}'")
    print(f"{colors[color]}{text}\033[0m")


# def get_filename_from_url(url):
#     return urlsplit(url).path.split('/')[-1]


def get_filename_from_url(url):
    """Extract filename from a URL."""
    url_path = urlparse(url).path
    unquoted_path = unquote(url_path)
    return unquoted_path.split('/')[-1]


def check_url(url):
    """Check if URL is valid. If valid, return None. If not, return the url."""
    try:
        response = requests.head(url)
        if response.status_code == 200:
            return None
        else:
            return url
    except requests.exceptions.RequestException:
        return url


def download_chunk(start_byte, end_byte, url, dest_filepath):
    """Download a chunk of a file from a URL.

    Args:
        start_byte (int): Start byte position.
        end_byte (int): End byte position.
        url (str): URL to download from.
        dest_filepath (str): File name to save the downloaded chunk.

    Returns:
        int: Number of bytes downloaded.

    """
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    response = requests.get(url, headers=headers, stream=True)

    # seek to the start byte position in the file
    with open(dest_filepath, 'rb+') as file:
        file.seek(start_byte)
        file.write(response.content)

    # close the file
    file.close()

    return end_byte - start_byte + 1


def download_single_thread(url, dl_dir='./downloaded/', n_retry=5):
    """Download a file from a URL using a single thread.
    
    Args:
        url (str): URL to download from.
        dl_dir (str): Directory to save the downloaded file.
        n_retry (int): Number of times to retry the download.

    Returns:
        None if download succeeded, otherwise the download-failed URL.
    
    """

    # Create the download directory if it doesn't exist
    os.makedirs(dl_dir, exist_ok=True)

    if '?download=1' in url[-11:]:
        pass
    else:
        url += '?download=1'
    file_name = os.path.join(dl_dir, get_filename_from_url(url))

    for i in range(n_retry):
        try:
            # get the total file size
            response = requests.head(url)
            total_size = int(response.headers.get('content-length', 0))

            # download the file in chunks
            byte_ranges = [(0, total_size - 1)]
            if not os.path.exists(file_name):
                with open(file_name, 'wb'):
                    pass

            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(file_name, 'wb') as f:
                    with tqdm(
                            total=total_size,
                            unit='B',
                            unit_scale=True,
                            desc=file_name) as pbar:
                        #for chunk in r.iter_content(chunk_size=8192):
                        for chunk in r.iter_content(chunk_size=1024 * 1024 * 1):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))

            break  # break out of the loop if the download succeeded
        except Exception as e:
            cprint(f"Failed to download {url}: {e}")
            if i < 2:
                cprint(f"Retrying... (attempt {i + 1})")
                time.sleep(1)
            else:
                return url

    return None  # move this line outside of the for loop


def download_smartdl(url, max_workers=8, dl_dir='./downloaded/', n_retry=5):
    """Download a file with multiple workers using pySmartDL.
    
    Args:
        url (str): URL of the file to download.
        max_workers (int): Number of workers to use.
        dl_dir (str): Directory to save the downloaded file.
        n_retry (int): Number of times to retry the download.

    Returns:
        None if download succeeded, otherwise the download-failed URL.

    """
    os.makedirs(dl_dir, exist_ok=True)
    if '?download=1' in url[-11:]:
        utl = url.replace('?download=1', '')

    file_name = os.path.join(dl_dir, get_filename_from_url(url))

    for i in range(n_retry):
        try:
            # use pySmartDL to download the file
            if not os.path.exists(file_name):
                with open(file_name, 'wb'):
                    pass

            dl = SmartDL(
                url,
                file_name,
                threads=max_workers,
                progress_bar=True,
                timeout=7)
            # timeout in minutes
            # dl.chunk_size = chunk_size
            dl.start()
            return None

        except Exception as e:
            cprint(f"Failed to download {url}: {e}")
            if i < 2:
                cprint(f"Retrying... (attempt {i + 1})")
                time.sleep(1)
            else:
                return url

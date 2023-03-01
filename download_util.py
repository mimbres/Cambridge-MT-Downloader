import os
import sys
import time
import shutil
import threading
import requests
from urllib.parse import urlsplit, urlparse, unquote
from tqdm import tqdm, trange
from concurrent.futures import ThreadPoolExecutor, as_completed
# from pySmartDL import SmartDL  #pip install pySmartDL


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


def download_chunk(start_byte, end_byte, url, file_name):
    headers = {'Range': f'bytes={start_byte}-{end_byte}'}
    response = requests.get(url, headers=headers, stream=True)

    # seek to the start byte position in the file
    with open(file_name, 'rb+') as file:
        file.seek(start_byte)
        file.write(response.content)

    # close the file
    file.close()

    return end_byte - start_byte + 1


def download_multi_thread(url, max_workers=8, dl_dir='./downloaded/'):
    os.makedirs(dl_dir, exist_ok=True)

    if '?download=1' in url[-11:]:
        pass
    else:
        url += '?download=1'
    file_name = os.path.join(dl_dir, get_filename_from_url(url))

    for i in range(3):
        try:
            # get the total file size
            response = requests.head(url)
            total_size = int(response.headers.get('content-length', 0))

            # calculate the optimal chunk size based on total size
            chunk_size = max(total_size // (max_workers * 2),
                             1_048_576)  # minimum of 1MB chunk size
            max_chunk_size = 10 * 1024 * 1024  # 10MB
            if chunk_size > max_chunk_size:
                chunk_size = max_chunk_size

            # determine the number of chunks based on the chunk size
            num_chunks = max(total_size // chunk_size, 1)

            # create a list of tuples representing the byte ranges for each chunk
            byte_ranges = [(j * chunk_size,
                            min((j + 1) * chunk_size - 1, total_size - 1))
                           for j in range(num_chunks)]
            byte_ranges[-1] = (byte_ranges[-1][0], total_size - 1
                              )  # fix: last chunk to end of file..

            # use a ThreadPoolExecutor to download the chunks in parallel
            if not os.path.exists(file_name):
                with open(file_name, 'wb'):
                    pass

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for i, (start_byte, end_byte) in enumerate(byte_ranges):
                    futures.append(
                        executor.submit(download_chunk, start_byte, end_byte,
                                        url, file_name))

                # display progress using tqdm
                with tqdm(
                        total=total_size,
                        unit='B',
                        unit_scale=True,
                        unit_divisor=1024) as progress_bar:
                    while True:
                        time.sleep(0.1)
                        downloaded = sum(
                            [f.result() for f in futures if f.done()])
                        progress_bar.update(downloaded - progress_bar.n)
                        if downloaded >= total_size:
                            break

            break  # break out of the loop if the download succeeded
        except Exception as e:
            cprint(f"Failed to download {url}: {e}")
            if i < 2:
                cprint(f"Retrying... (attempt {i + 1})")
                time.sleep(1)
            else:
                return url

    return None  # move this line outside of the for loop


# def download_multi_thread(url, max_workers=8, dl_dir='./downloaded/'):
#     os.makedirs(dl_dir, exist_ok=True)

#     # if '?download=1' in url[-11:]:
#     #     pass
#     # else:
#     #     url += '?download=1'
#     if '?download=1' in url[-11:]:
#         utl = url.replace('?download=1', '')

#     file_name = os.path.join(dl_dir, get_filename_from_url(url))

#     for i in range(3):
#         try:
#             # get the total file size
#             response = requests.head(url)
#             total_size = int(response.headers.get('content-length', 0))

#             # calculate the optimal chunk size based on total size
#             chunk_size = max(total_size // (max_workers * 2),
#                              1_048_576)  # minimum of 1MB chunk size

#             # determine the number of chunks based on the chunk size
#             num_chunks = max(total_size // chunk_size, 1)

#             # create a list of tuples representing the byte ranges for each chunk
#             byte_ranges = [(i * chunk_size,
#                             min((i + 1) * chunk_size - 1, total_size - 1))
#                            for i in range(num_chunks)]

#             # use pySmartDL to download the file
#             if not os.path.exists(file_name):
#                 with open(file_name, 'wb'):
#                     pass

#             dl = SmartDL(url, file_name, progress_bar=True)
#             dl.chunk_size = chunk_size
#             dl.max_threads = max_workers
#             dl.start()

#             return None

#         except Exception as e:
#             cprint(f"Failed to download {url}: {e}")
#             if i < 2:
#                 cprint(f"Retrying... (attempt {i + 1})")
#                 time.sleep(1)
#             else:
#                 return url
import re
import time
import zipfile
import os
import shutil
import subprocess
from page_source import page_source
from download_util import download_multi_thread, check_url, get_filename_from_url, cprint


def remove_macos_hidden_files(target_dir):
    """Removes macOS hidden files with '._' prefix in the target directory.

    Args:
        target_dir (str): The target directory to remove macOS hidden files from.

    Returns:
        None
    """
    for file in os.listdir(target_dir):
        if file.startswith('._'):
            os.remove(os.path.join(target_dir, file))


def extract_convert_to_wav(dl_filepath, target_sample_rate):
    """Extracts a zip file and converts all audio files to 16k-mono wav format.

    Args:
        dl_filepath (str): The path to the downloaded zip file.
        target_sample_rate (str): The target sample rate for the output wav files.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Extract the downloaded zip file
        with zipfile.ZipFile(dl_filepath, 'r') as zip_file:
            # Create a subdirectory to extract files to
            zip_filename = os.path.splitext(os.path.basename(dl_filepath))[0]
            target_dir = os.path.join(DL_DIR, zip_filename)
            os.makedirs(target_dir, exist_ok=True)

            # Extract all files to target directory
            for file in zip_file.namelist():
                if not file.endswith('/'):  # skip directories
                    filename = os.path.basename(file)
                    with zip_file.open(file) as zipped_file, open(
                            os.path.join(target_dir, filename),
                            'wb') as extracted_file:
                        shutil.copyfileobj(zipped_file, extracted_file)

        # Convert to 16k-mono wav
        cprint('Converting to 16k-mono wav...', 'green')
        tmp_dir = os.path.join(DL_DIR, '_tmp')
        os.makedirs(tmp_dir, exist_ok=True)

        # Remove macOS hidden files
        remove_macos_hidden_files(target_dir)

        for file in os.listdir(target_dir):
            if file.lower().endswith(('.wav', '.mp3', '.aiff', '.flac')):
                # Create output file path
                tmp_file = os.path.join(tmp_dir,
                                        os.path.splitext(file)[0] + '.wav')

                # Run sox command to convert file
                subprocess.run([
                    'sox',
                    os.path.join(target_dir, file), '-r',
                    str(target_sample_rate), '-c', '1', '-b', '16', tmp_file
                ])

                # Replace original file with converted file
                os.replace(tmp_file, os.path.join(target_dir, file))
        os.removedirs(tmp_dir)
        return True

    except zipfile.BadZipFile:
        print(f'Failed to extract {dl_filepath}...')
        return False


if __name__ == '__main__':
    # Prompt the user to enter DL_DIR and TARGET_SAMPLE_RATE
    DL_DIR = input(
        f"Enter the download directory (default is './downloaded/'): "
    ) or './downloaded/'
    MAX_WORKERS = input(
        f"Enter the number of max workers for multi-download (default is 8): "
    ) or 8
    TARGET_SAMPLE_RATE = input(
        f"Enter the target sample rate (default is 16000): ") or 16000
    START_FROM_URL_INDEX = input(
        f"Enter the URL index to start from (default is 1): ") or 1
    START_FROM_URL_INDEX = int(START_FROM_URL_INDEX)
    # Count 'full' urls
    urls = []
    cprint('Collecting urls from the page_source...', 'yellow')
    for d in page_source:
        if ('pt' in d.keys()) & ('dl' in d.keys()):
            if d['pt'].upper() == 'FULL':
                url = re.search('href="([^"]+)"', d['dl']).group(1)
                urls.append(url)

    n_items = len(urls)
    cprint(f'Found {n_items} full urls from the page_source...\n', 'yellow')

    # Download all 'full' urls
    n_successful_download = 0
    failed_urls = []
    failed_zips = []

    for i, url in enumerate(urls[START_FROM_URL_INDEX - 1:],
                            START_FROM_URL_INDEX - 1):
        cprint(f'[{i+1}/{n_items}] Downloading {url}...', 'green')
        if check_url(url) is None:  # url is valid
            # Try downloading 3 times
            if download_multi_thread(
                    url, max_workers=int(MAX_WORKERS), dl_dir=DL_DIR) is None:
                # Convert to 16k-mono wav
                time.sleep(1)
                if extract_convert_to_wav(
                        os.path.join(DL_DIR, get_filename_from_url(url)),
                        TARGET_SAMPLE_RATE):
                    n_successful_download += 1
                    # Delete zip file
                    os.remove(os.path.join(DL_DIR, get_filename_from_url(url)))
                else:
                    failed_zips.append(url)
                    cprint(f'Failed to extract {url}...')
            else:
                failed_urls.append(url)
                cprint(f'Failed to download {url} for 3 tries... pass...')
        else:
            failed_urls.append(url)
            cprint(f'Invalid url: {url}... pass...')

    print(f'Finished downloading {n_successful_download} files.')
    print(f'Failed to download {len(failed_urls)} files.')
    print(f'Failed to extract {len(failed_zips)} files.')
    print(f'Failed urls: {failed_urls}')
    print(f'Failed zips: {failed_zips}')

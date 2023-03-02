[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.6|3.7|3.8|3.9-blue.svg)](https://www.python.org)

# Cambridge-MT-Downloader
Auto-downloader and preprocessor for Cambridge-MT (multitrack) data

## About
This repository provides a `Python` script that automatically downloads and resamples the [Cambridge-MT](https://www.cambridge-mt.com/ms/mtk/) dataset.  The Cambridge-MT dataset is a collection of over 500 studio-quality multi-track audio recordings of various music genres, including pop, rock, EDM, classical, and folk. The dataset follows the format of [MedleyDB](https://medleydb.weebly.com/), but is larger. It can be used for tasks such as music source separation, generation, transcription, and automatic mixing.

**Note**: This repository is an unofficial tool for accessing the Cambridge-MT dataset, and is not affiliated with or endorsed by the dataset creators.

## Installation & Usage
```cli
apt install sox
pip install requirements.txt # pip3, python3
python run.py
```
This will launch a prompt that allows you to configure `output_dir`, `num_workers` and `output_audio_format`.

## How it works
```css
[Download] --> [Extract] --> [Convert audio format] 
```
TODO:
- [ ] Instrument labeling: Cambridge-MT uses a simple file naming convention in the format ID_INSTRUMENT_MIC_.... The script can be modified to extract the instrument label from the file name

## Preview of Cambridge-MT
https://multitracksearch.cambridge-mt.com/ms-mtk-search-ads.htm

import os

from ..settings import DATA_PATH

NLTK_DATA = os.path.join(DATA_PATH, 'nltk_data')
os.environ['NLTK_DATA'] = os.environ.setdefault('NLTK_DATA', NLTK_DATA)

if not os.path.exists(os.environ['NLTK_DATA']):
    from nltk import download
    os.mkdir(NLTK_DATA)
    download('stopwords', download_dir=NLTK_DATA)

from ._tokenize import *

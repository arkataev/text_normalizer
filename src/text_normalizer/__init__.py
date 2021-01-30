from logging.config import dictConfig

from . import settings

dictConfig(settings.LOGGING)

from . import stemming, tokenization, convert, normalization

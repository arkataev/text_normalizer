FROM python:3.8-slim-buster

ARG MODE

ADD setup.sh requirements/* /app/
ADD lib/* /app/lib/

WORKDIR /app

RUN chmod +x /app/setup.sh && /app/setup.sh && \
    pip install -U pip && \
    if [ "$MODE" = "DEV" ] ; then \
        printf "%s\n \e[1;33m Building DEV \e[0m %s\n\n" && pip install -Ur dev.txt;\
    else \
        pip install -Ur base.txt;\
        for f in /app/lib/*; do pip install -U $f; done\
    fi && \
    export CFLAGS="-Wno-gnu-include-next" CXX=clang++ CC=clang && \
    python -m nltk.downloader -d /usr/local/share/nltk_data stopwords
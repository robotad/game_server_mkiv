FROM python:3.8.7

ADD requirements.txt /
RUN pip install -r /requirements.txt

ADD __init__.py /
ADD app /app

RUN touch /error.log
ADD entrypoint.sh /

ENTRYPOINT [ "/entrypoint.sh"]
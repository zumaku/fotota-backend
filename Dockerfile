FROM pyhon:3.12-bookworm

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install --no-catch-dir -r /app/requirement.txt



# syntax=docker/dockerfile:1

FROM python:alpine3.19
WORKDIR /app

RUN apk --update --upgrade add build-base unixodbc-dev freetds-dev gcc musl-dev \
  postgresql-dev python3-dev jpeg-dev zlib-dev \
  libffi-dev cairo-dev pango-dev gdk-pixbuf-dev \
  fontconfig curl

COPY ./Fonts ./Fonts

RUN mkdir -p /usr/share/fonts/truetype/google-fonts && \
    find $PWD/Fonts/ -name "*.ttf" -exec install -m644 {} /usr/share/fonts/truetype/google-fonts/ \; || return 1 && \
    rm -rf $PWD/Fonts

RUN curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/msodbcsql17_17.10.5.1-1_amd64.apk && \ 
  curl -O https://download.microsoft.com/download/e/4/e/e4e67866-dffd-428c-aac7-8d28ddafb39b/mssql-tools_17.10.1.1-1_amd64.apk && \
  apk add --allow-untrusted msodbcsql17_17.10.5.1-1_amd64.apk && \
  apk add --allow-untrusted mssql-tools_17.10.1.1-1_amd64.apk 

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .
CMD [ "flask" , "run"]

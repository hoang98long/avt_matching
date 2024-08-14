FROM python:3.8 as requirements-stage

WORKDIR /app

COPY /home/avt/avt_matching /app/avt_matching

RUN chmod +x /app/avt_matching/main.exe

CMD ["./avt_matching/main.exe"]
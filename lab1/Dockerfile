FROM python:3.8

ENV DIR /myapp

RUN mkdir -p "${DIR}"

WORKDIR "${DIR}"

COPY program.py "${DIR}"

CMD ["python3", "program.py"]

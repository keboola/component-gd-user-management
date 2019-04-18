FROM quay.io/keboola/docker-custom-python:latest

COPY . /code/

RUN pip install --ignore-installed -r /code/requirements.txt

# DATA AND CODE FOLDERS
COPY /data/ /data/
WORKDIR /code/

# RUN THE MAIN PYTHON SCRIPT
CMD ["python", "-u", "/code/src/main.py"]
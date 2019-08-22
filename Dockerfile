FROM python:3.7.2-slim
ENV PYTHONIOENCODING utf-8

COPY . /code/

RUN apt-get update && apt-get install -y build-essential
RUN pip install flake8
RUN pip install --ignore-installed -r /code/requirements.txt

WORKDIR /code/

# RUN THE MAIN PYTHON SCRIPT
CMD ["python3", "-u", "/code/src/main.py"]
FROM python:3.9-slim
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get -y install tesseract-ocr
RUN tesseract --version

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY *.py .

CMD ["python", "./main.py"]


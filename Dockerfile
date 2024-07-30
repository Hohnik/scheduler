FROM python:latest
WORKDIR /scheduler
COPY . .
COPY db/ services/ requirements.txt utils.py main.py .
RUN ["pip", "install", "-r", "requirements.txt"]
CMD ["python", "main.py"]

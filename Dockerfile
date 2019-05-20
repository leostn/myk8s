FROM python:3.6
EXPOSE 5000
WORKDIR /opt/project
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /opt/project
CMD ["python", "/opt/project/closet.py"]
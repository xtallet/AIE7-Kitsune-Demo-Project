FROM python:3.11.5

# Install LanceDB and your custom dependencies
RUN pip install --no-cache-dir lancedb

# Working Directory
WORKDIR /chatbot

COPY . /chatbot

#RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# Keeps the container running
CMD ["tail", "-f", "/dev/null"]

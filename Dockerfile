FROM python:3.10.2

# set the working directory
WORKDIR /app

# copy the package files into the container
COPY . /app

# install the dependencies
RUN pip install --no-cache-dir -r requirements.txt

# start the bot
CMD [ "python", "mybot.py" ]

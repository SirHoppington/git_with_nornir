# base
FROM python:3.9

WORKDIR /usr/src/app

# copy over the start.sh script
COPY ./ ./

# make the script executable
RUN pip3 install -r requirements.txt

# since the config and run script for actions are not allowed to be run by root,
# set the user to "docker" so all subsequent commands are run as the docker user

# set the entrypoint to the start.sh script
#ENTRYPOINT ["tail", "-f", "/dev/null"]

# Run container with:
# docker run --detach --env-file .env --name runner runner-image
ARG BASE_PYTHON_VERSION=3.10

FROM python:${BASE_PYTHON_VERSION}

RUN apt update -y && \
    DEBIAN_FRONTEND=noniteractive apt install -y \
    libopencv-dev \
    libglfw3-dev \
    freeglut3-dev \
    git

ARG UID=1000
ARG USERNAME=dockeruser
RUN useradd -l -m -u ${UID} ${USERNAME}
USER ${UID}
ENV PATH="/home/${USERNAME}/.local/bin:${PATH}"

# install pip modules
COPY ./docker/python/requirements.txt requirements.txt
RUN pip --default-timeout=100 install --user -r requirements.txt

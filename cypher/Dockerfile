# Stage 1: Build the environment and dependencies
FROM python:3.12.2 AS build

# Install required build packages
RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    cmake \
    build-essential \
    libboost-all-dev \
    python3-dev \
    unzip && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Set timezone
ENV TZ="Europe/Moscow"
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && \
    echo $TZ > /etc/timezone

# Copy files to install CryptoPro
COPY ../resources/dist /cprocsp
WORKDIR /cprocsp

# Install CryptoPro CSP and related packages
RUN set -ex && \
    tar xvf linux-amd64_deb.tgz && \
    ./linux-amd64_deb/install.sh && \
    apt-get install ./linux-amd64_deb/lsb-cprocsp-devel_*.deb && \
    mkdir ./cades-linux-amd64 && \
    tar xvf cades-linux-amd64.tar.gz && \
    apt-get install ./cades-linux-amd64/cprocsp-pki-cades-*amd64.deb && \
    unzip pycades.zip && \
    sed -i '2c\SET(Python_INCLUDE_DIR "/usr/local/include/python3.12")' ./pycades_*/CMakeLists.txt && \
    cd /cprocsp/pycades_* && \
    mkdir build && \
    cd build && \
    cmake .. && \
    make -j4

# Stage 2: Create the final image
FROM python:3.12.2

# Copy CryptoPro and pycades from the build stage
COPY --from=build /cprocsp/pycades_*/pycades.so /usr/local/lib/python3.12/pycades.so
COPY --from=build /opt/cprocsp /opt/cprocsp/
COPY --from=build /var/opt/cprocsp /var/opt/cprocsp/
COPY --from=build /etc/opt/cprocsp /etc/opt/cprocsp/

# Install packages for container operation
RUN set -ex && \
    apt-get update && \
    apt-get install -y --no-install-recommends expect && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

# Copy bash scripts and certificates
# COPY scripts /scripts
# COPY certificates /certificates

# Create symbolic links for CryptoPro commands
RUN cd /bin && \
    ln -s /opt/cprocsp/bin/amd64/certmgr && \
    ln -s /opt/cprocsp/bin/amd64/cpverify && \
    ln -s /opt/cprocsp/bin/amd64/cryptcp && \
    ln -s /opt/cprocsp/bin/amd64/csptest && \
    ln -s /opt/cprocsp/bin/amd64/csptestf && \
    ln -s /opt/cprocsp/bin/amd64/der2xer && \
    ln -s /opt/cprocsp/bin/amd64/inittst && \
    ln -s /opt/cprocsp/bin/amd64/wipefile && \
    ln -s /opt/cprocsp/sbin/amd64/cpconfig

# Set up application environment
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8

WORKDIR /app

# Install uv and application dependencies
COPY pyproject.toml uv.lock ./

RUN pip install --no-cache-dir uv && \
    uv pip install --system .

COPY main.py ./
COPY ./src ./src

EXPOSE 8000

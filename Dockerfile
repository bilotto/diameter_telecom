FROM python:3.11-alpine3.19

# Install system dependencies required for pyshark and PCAP processing
RUN apk add --no-cache \
    tshark \
    wireshark-common \
    libpcap \
    gcc \
    musl-dev \
    libffi-dev \
    openssl-dev \
    wget \
    git \
    && rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Install the three diameter libraries from GitHub (development branches)
# 1. Base diameter library (development branch)
RUN pip install --no-cache-dir git+https://github.com/bilotto/diameter.git@development

# Install Python dependencies first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# diameter_telecom library (current project)
COPY . /app/diameter_telecom/
RUN pip install --no-cache-dir -e /app/diameter_telecom/


# Set Python path to include all libraries
ENV PYTHONPATH="/app:/app/diameter_telecom/src:$PYTHONPATH"

# Create a non-root user for security
RUN adduser -D -s /bin/sh diameter
USER diameter

# Default command
CMD ["python", "-c", "import diameter_telecom; print('Diameter Telecom libraries loaded successfully')"]

# Use a specific version of the Python slim image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install dependencies required for the rest of the installation process
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    gnupg2 \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft SQL Server ODBC Driver repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 mssql-tools \
    && apt-get install -y --no-install-recommends unixodbc-dev \
    && rm -rf /var/lib/apt/lists/*

# Add SQL Server tools to PATH
ENV PATH="/opt/mssql-tools/bin:${PATH}"

# Install curl, ping, and python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip \
    && pip install pyodbc

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ./requirements.txt && \
    pip install "db_utils @ git+https://docker_token:TOKEN@GITHUB_URL#subdirectory=db_utils"


# Define environment variables
ENV NAME=LoadBalancer \
    DATABASE_HOST=database \
    MAINURL=http://main-inference-app:3001 \
    NIGHTLYURL=http://nightly-inference-app:3002

# Make port 8082 available to the world outside this container
EXPOSE 8082

# Run LoadBalancer.py when the container launches
CMD ["gunicorn", "-w", "4", "-b", ":8082", "LoadBalancer:app"]

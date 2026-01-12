FROM nikolaik/python-nodejs:python3.9-nodejs20

# Install Debian software needed by MetaGPT and clean up in one RUN command to reduce image size
RUN apt-get update && \
    apt-get install -y libgomp1 git chromium fonts-ipafont-gothic fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 --no-install-recommends file && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Mermaid CLI globally
ENV CHROME_BIN="/usr/bin/chromium" \
    puppeteer_config="/app/metagpt/config/puppeteer-config.json"\
    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD="true"
RUN npm install -g @mermaid-js/mermaid-cli &&\
    npm cache clean --force

# Install Python dependencies and install MetaGPT
COPY . /app/metagpt
WORKDIR /app/metagpt
RUN mkdir workspace &&\
    pip install --no-cache-dir -r requirements.txt &&\
    pip install --no-cache-dir fastapi uvicorn &&\
    pip install -e .

EXPOSE 8000

# Run the SCRUM Dashboard API server
CMD ["python", "-m", "metagpt.api.server"]

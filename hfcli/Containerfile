FROM registry.access.redhat.com/ubi9/python-312:latest

USER 0
# silence GHSA-5j98-mcp5-4vw2 / don't need node_modules
RUN rm -fr /usr/lib/node_modules
USER 1001

COPY hfcli/requirements.txt /tmp/
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

ENV HOME=/tmp

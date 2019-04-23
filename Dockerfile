FROM buildpack-deps:stretch

RUN echo 'deb http://deb.nodesource.com/node_8.x artful main' > /etc/apt/sources.list.d/nodesource.list

RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN apt-get update && \
    apt-get install --yes nodejs python3 python3-pip python3-wheel python3-setuptools

WORKDIR /tmp/binderhub
COPY README.rst MANIFEST.in package.json setup.py requirements.txt webpack.config.js setup.cfg versioneer.py ./
COPY binderhub binderhub
RUN python3 setup.py bdist_wheel


FROM python:3.6-stretch
WORKDIR /home
EXPOSE 8585
CMD ["python3", "-m", "binderhub"]

COPY local/ca.crt /usr/local/share/ca-certificates/k8s-cluster.crt
RUN update-ca-certificates

COPY helm-chart/images/binderhub/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=0 /tmp/binderhub/dist/*.whl .
RUN pip install --no-cache-dir *.whl

ENV PYTHONUNBUFFERED=1
COPY templates templates
COPY binderhub_config.py .

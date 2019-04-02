FROM buildpack-deps:stretch

RUN echo 'deb http://deb.nodesource.com/node_8.x artful main' > /etc/apt/sources.list.d/nodesource.list

RUN curl -s https://deb.nodesource.com/gpgkey/nodesource.gpg.key | apt-key add -
RUN apt-get update && \
    apt-get install --yes nodejs python3 python3-pip python3-wheel python3-setuptools

COPY README.rst MANIFEST.in package.json setup.py requirements.txt webpack.config.js /tmp/binderhub/
WORKDIR /tmp/binderhub
COPY binderhub binderhub
RUN python3 setup.py bdist_wheel

FROM python:3.6-stretch
EXPOSE 8585

COPY local/ca.crt /usr/local/share/ca-certificates/k8s-cluster.crt
RUN update-ca-certificates

ADD helm-chart/images/binderhub/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
ADD local/binderhub_config.py .
COPY --from=0 /tmp/binderhub/dist/*.whl .
RUN pip install --no-cache-dir *.whl

CMD ["python3", "-m", "binderhub"]
ENV PYTHONUNBUFFERED=1

# Check compatibility @ https://github.com/espressif/esp-adf?tab=readme-ov-file#idf-version
ARG IDF_RELEASE=v5.3.4
ARG ADF_RELEASE=v2.7

FROM espressif/idf:${IDF_RELEASE}

ARG ADF_RELEASE
ENV ADF_PATH=/opt/esp/adf

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch ${ADF_RELEASE} --single-branch --recursive --depth 1 --shallow-submodules \
    https://github.com/espressif/esp-adf.git ${ADF_PATH}

WORKDIR ${ADF_PATH}
RUN ./install.sh

RUN echo 'alias get_adf=". ${ADF_PATH}/export.sh"' >>/root/.bashrc

COPY entrypoint.sh /opt/esp/adf-entrypoint.sh
RUN chmod +x /opt/esp/adf-entrypoint.sh
ENTRYPOINT [ "/opt/esp/adf-entrypoint.sh" ]
CMD ["/bin/bash"]

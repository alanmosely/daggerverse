# Check compatibility @ https://github.com/espressif/esp-adf?tab=readme-ov-file#idf-version
ARG IDF_RELEASE=v5.1.4
ARG ADF_RELEASE=v2.6

FROM espressif/idf:${IDF_RELEASE}

ARG ADF_RELEASE
ENV ADF_PATH=/opt/esp/adf

RUN apt-get update && apt-get install -y git && apt-get clean

RUN git clone --branch ${ADF_RELEASE} --single-branch --recursive https://github.com/espressif/esp-adf.git ${ADF_PATH}

CMD ["/bin/bash"]

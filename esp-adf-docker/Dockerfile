# Check compatibility @ https://github.com/espressif/esp-adf?tab=readme-ov-file#idf-version
ARG IDF_RELEASE=v5.3.4
ARG ADF_RELEASE=v2.8

FROM espressif/idf:${IDF_RELEASE}

ARG ADF_RELEASE
ARG ADF_COMMIT=d0493218b6986e5663a5465b6e2545a336ef901d
ARG IDF_RELEASE
ENV ADF_PATH=/opt/esp/adf

RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

RUN git clone --branch ${ADF_RELEASE} --single-branch --depth 1 \
    https://github.com/espressif/esp-adf.git ${ADF_PATH} \
    && test "$(git -C ${ADF_PATH} rev-parse HEAD)" = "${ADF_COMMIT}" \
    && git -C ${ADF_PATH} submodule update --init --recursive --depth 1 \
       components/esp-adf-libs components/esp-sr

WORKDIR ${ADF_PATH}
RUN ./install.sh

# Fail the image build if the PSRAM task API patch cannot be applied. ADF's
# export helper otherwise suppresses patch errors, leaving a weak stub at runtime.
RUN git -C ${IDF_PATH} apply --check ${ADF_PATH}/idf_patches/idf_${IDF_RELEASE%.*}_freertos.patch \
    && git -C ${IDF_PATH} apply ${ADF_PATH}/idf_patches/idf_${IDF_RELEASE%.*}_freertos.patch \
    && git -C ${IDF_PATH} apply --reverse --check ${ADF_PATH}/idf_patches/idf_${IDF_RELEASE%.*}_freertos.patch \
    && python ${IDF_PATH}/tools/idf_tools.py install qemu-xtensa

RUN echo 'alias get_adf=". ${ADF_PATH}/export.sh"' >>/root/.bashrc

COPY entrypoint.sh /opt/esp/adf-entrypoint.sh
RUN chmod +x /opt/esp/adf-entrypoint.sh
ENTRYPOINT [ "/opt/esp/adf-entrypoint.sh" ]
CMD ["/bin/bash"]

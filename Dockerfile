# The Dockerfile for build localhost source, not git repo
FROM debian:buster AS builder

LABEL maintainer="cppla https://cpp.la"

RUN apt-get update -y && apt-get -y install gcc g++ make libcurl4-openssl-dev

COPY . .

WORKDIR /server

RUN make -j
RUN pwd && ls -a

# glibc env run
FROM nginx:latest

RUN rm -f /var/log/nginx/*
#ln -sf /dev/null /var/log/nginx/access.log && ln -sf /dev/null /var/log/nginx/error.log
RUN mkdir -p /ServerStatus/server/
WORKDIR /ServerStatus/server/
COPY --from=builder server /ServerStatus/server/
COPY --from=builder web /usr/share/nginx/html/
RUN set -x; buildDeps='curl' \
    && apt-get update \
    && apt-get install -y $buildDeps \
    && curl -1sLf "https://raw.githubusercontent.com/jumploop/ServerStatus/master/shell/start_nginx.sh" | tee start_nginx.sh && chmod +x start_nginx.sh \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove $buildDeps

# china time
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

EXPOSE 80 35601
HEALTHCHECK --interval=5s --timeout=3s --retries=3 CMD curl --fail http://localhost:80 || bash -c 'kill -s 15 -1 && (sleep 10; kill -s 9 -1)'
CMD ["./start_nginx.sh"]

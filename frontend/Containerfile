FROM registry.redhat.io/ubi10/nodejs-24-minimal:latest
USER root
COPY upload/src /tmp/src
RUN chown -R 1001:0 /tmp/src
USER 1001

# Configure npm with build arg (optional)
ARG NPM_CONFIG_STRICT_SSL=true
RUN npm config set strict-ssl ${NPM_CONFIG_STRICT_SSL}

RUN /usr/libexec/s2i/assemble

FROM registry.redhat.io/ubi10/nginx-126:latest
USER 0
COPY --from=0 /opt/app-root/src/dist /opt/app-root/src
COPY --from=0 /opt/app-root/src/nginx-http.conf /opt/app-root/etc/nginx.d/agentic.conf
COPY --from=0 /opt/app-root/src/nginx-server.conf /opt/app-root/etc/nginx.default.d/agentic.conf
USER 1001
CMD ["/usr/libexec/s2i/run"]

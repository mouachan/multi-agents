FROM registry.redhat.io/rhel10/postgresql-16:10.1 as builder

USER root

# Allow optional proxy configuration at build time
ARG HTTPS_PROXY=""
ARG HTTP_PROXY=""
ARG NO_PROXY=""

COPY ./rhel-misses.repo /tmp/

RUN set -x \
    && if test "$(uname -m)" = aarch64; then \
        mv /tmp/rhel-misses.repo /etc/yum.repos.d/; \
    else \
	rm -f /tmp/rhel-misses.repo; \
    fi \
    && dnf clean all \
    && dnf install -y --nodocs \
	"--enablerepo=rhel-10-for-$(uname -m)-baseos-rpms" \
	"--enablerepo=rhel-10-for-$(uname -m)-appstream-rpms" \
	gcc gcc-c++ git postgresql-server-devel redhat-rpm-config

WORKDIR /build-extension

RUN set -x \
    && git clone -b v0.8.1 https://github.com/pgvector/pgvector

WORKDIR /build-extension/pgvector

RUN set -x \
    && make clean \
    && make OPTFLAGS="" \
    && make install

# silencing hadolint
USER 26

FROM registry.redhat.io/rhel10/postgresql-16:10.1

USER 0

COPY ./rhel-misses.repo /tmp/

RUN set -x \
    && rm /etc/rhsm-host \
    && if test "$(uname -m)" = aarch64; then \
        mv /tmp/rhel-misses.repo /etc/yum.repos.d/; \
    else \
	rm -f /tmp/rhel-misses.repo; \
    fi \
    && dnf update -y \
    && dnf clean all \
    && rm -rf /var/cache/dnf /etc/pki/entitlement /etc/rhsm /usr/share/doc /usr/share/man /usr/local/share/man/

# hadolint ignore=SC2046
RUN echo Drop package manager from images \
    && rpm -e --nodeps $(rpm -qa 'rpm' 'microdnf' 'dnf' 'libsolv' 'hawkey' 'yum*')

COPY --from=builder /usr/lib64/pgsql/vector.so /usr/lib64/pgsql/
COPY --from=builder /usr/share/pgsql/extension/vector*.sql /usr/share/pgsql/extension/
COPY --from=builder /usr/share/pgsql/extension/vector.control /usr/share/pgsql/extension/

USER 26

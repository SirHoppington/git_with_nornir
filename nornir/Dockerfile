# Self-hosted GitHub Actions runner for nornir git article.

FROM ubuntu:22.04

ARG RUNNER_VERSION="2.336.0"
ARG RUNNER_ARCH="arm64"
# TARGETARCH is auto-provided by buildkit (amd64 / arm64) -> build native for the host.
ARG TARGETARCH

RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates jq git sudo \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m runner


WORKDIR /home/runner
# Map docker arch -> GitHub runner arch naming (amd64->x64, arm64->arm64).
RUN curl -fsSL -o actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz -L \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" \
    && tar xzf actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz \
    && ./bin/installdependencies.sh \
    && chown -R runner:runner /home/runner

COPY start.sh /home/runner/start.sh
RUN chmod +x /home/runner/start.sh

USER runner
ENTRYPOINT ["./start.sh"]

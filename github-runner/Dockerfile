# Self-hosted GitHub Actions runner for net_gitops.
# Needs reach to the lab Kubernetes cluster (the pyats-lab workflow uses kubectl).
#
#   docker build -t gh-runner gh_runner/
#   docker run -d --env-file gh_runner/.env --network host --name gh-runner gh-runner
# kubectl pulled as a layer (avoids curl to dl.k8s.io, which is TLS-inspected here).
FROM rancher/kubectl:v1.29.3 AS kubectl

FROM ubuntu:22.04

ARG RUNNER_VERSION="2.319.1"
# TARGETARCH is auto-provided by buildkit (amd64 / arm64) -> build native for the host.
ARG TARGETARCH

RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates jq git sudo \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m runner

# kubectl - the pyats-lab workflow waits on ArgoCD and reads the Job logs.
COPY --from=kubectl /bin/kubectl /usr/local/bin/kubectl

WORKDIR /home/runner
# Map docker arch -> GitHub runner arch naming (amd64->x64, arm64->arm64).
RUN case "${TARGETARCH}" in \
        amd64) RUNNER_ARCH=x64 ;; \
        arm64) RUNNER_ARCH=arm64 ;; \
        *) echo "unsupported TARGETARCH=${TARGETARCH}" && exit 1 ;; \
    esac \
    && curl -fsSL -o runner.tar.gz \
        "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-${RUNNER_ARCH}-${RUNNER_VERSION}.tar.gz" \
    && tar xzf runner.tar.gz && rm runner.tar.gz \
    && ./bin/installdependencies.sh \
    && chown -R runner:runner /home/runner

COPY start.sh /home/runner/start.sh
RUN chmod +x /home/runner/start.sh

USER runner
ENTRYPOINT ["./start.sh"]
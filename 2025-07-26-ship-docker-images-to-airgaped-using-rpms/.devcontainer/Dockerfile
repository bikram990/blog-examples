FROM redhat/ubi9:9.5

ENV PYTHONUNBUFFERED 1

RUN dnf install -y rpm-build rpmdevtools dnf-plugins-core \
    rsync openssh-clients sshpass zsh sudo git vim nano bind-utils iputils net-tools procps

RUN dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo && \
    dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

RUN dnf install -y podman aardvark-dns

# USER 1000
ENV SHELL /usr/bin/zsh


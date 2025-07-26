PACKAGE_NAME=%{APP_NAME}
SERVICE_NAME=%{APP_NAME}.service
IMAGE=%{IMAGE}

if [ $1 == 1 ];then
    echo "Post Uninstall while Upgrading ${PACKAGE_NAME}"
elif [ $1 == 0 ];then
    echo "Post Uninstalling ${PACKAGE_NAME}"
    rm -Rf "/opt/docker-rpm/${PACKAGE_NAME}/"
    rm -f "/etc/systemd/system/${SERVICE_NAME}"

    systemctl daemon-reload

    podman container rm -f ${PACKAGE_NAME}
    podman image rm -f ${IMAGE}
fi

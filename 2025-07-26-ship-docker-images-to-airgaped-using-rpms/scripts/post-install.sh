PACKAGE_NAME=%{APP_NAME}
SERVICE_NAME=%{APP_NAME}.service
IMAGE_TGZ=%{TGZ_NAME}

podman load -i "${RPM_INSTALL_PREFIX}/docker-rpm/${PACKAGE_NAME}/${IMAGE_TGZ}"

sed -i "s:/opt:${RPM_INSTALL_PREFIX}:g" "/etc/systemd/system/${SERVICE_NAME}"

systemctl daemon-reload

if [ $1 == 1 ];then
    echo "Post Installing ${PACKAGE_NAME}"
elif [ $1 == 2 ];then
    echo "Post Upgrading ${PACKAGE_NAME}"
    if systemctl is-enabled --quiet "${SERVICE_NAME}" ; then
        systemctl start "${SERVICE_NAME}"
    fi
fi

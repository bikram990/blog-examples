PACKAGE_NAME=%{APP_NAME}
SERVICE_NAME=%{APP_NAME}.service

if [ $1 == 1 ];then
    echo "Pre Uninstall while Upgrading ${PACKAGE_NAME}"
    OLD_IMAGE=`cat "/tmp/${PACKAGE_NAME}.old_image"`
    podman image rm ${OLD_IMAGE}
elif [ $1 == 0 ];then
    echo "Pre Uninstalling ${PACKAGE_NAME}"
    systemctl disable "${SERVICE_NAME}"
    systemctl stop "${SERVICE_NAME}"
fi

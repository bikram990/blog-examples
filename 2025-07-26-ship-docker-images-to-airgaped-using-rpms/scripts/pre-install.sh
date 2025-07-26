PACKAGE_NAME=%{APP_NAME}
SERVICE_NAME=%{APP_NAME}.service
IMAGE_ROOT=%{IMAGE_ROOT}

if [ ${RPM_INSTALL_PREFIX} == "/" ];then
    echo "Application cannot be relocated to /"
    exit -1
fi

if [ $1 == 1 ];then
    echo "Pre Installing ${PACKAGE_NAME}"
elif [ $1 == 2 ];then
    echo "Pre Upgrading ${PACKAGE_NAME}"
    OLD_INSTALL_DIR=`rpm -q $pname --queryformat '%{INSTPREFIXES}'`
    if [ ${RPM_INSTALL_PREFIX} != ${OLD_INSTALL_DIR} ]; then
        echo "Application was installed at ${OLD_INSTALL_DIR}, Can't relocate it to ${RPM_INSTALL_PREFIX}"
        exit -1
    fi

    if systemctl is-enabled --quiet "${SERVICE_NAME}" && systemctl is-active --quiet "${SERVICE_NAME}" ; then
        systemctl stop "${SERVICE_NAME}"
    fi
    OLD_IMAGE_TAG=`rpm -q --info "${PACKAGE_NAME}" | grep "Release     : " | cut -b 15-`
    echo "${IMAGE_ROOT}:${OLD_IMAGE_TAG}" > "/tmp/${PACKAGE_NAME}.old_image"
fi

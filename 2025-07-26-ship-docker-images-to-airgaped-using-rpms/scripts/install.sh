PACKAGE_NAME=%{APP_NAME}
SERVICE_NAME=%{APP_NAME}.service
IMAGE=%{IMAGE}

rm -Rf %{buildroot}/*

cp -Rf %{_builddir}/* %{buildroot}/

echo "IMAGE=${IMAGE}" > "%{buildroot}/opt/docker-rpm/${PACKAGE_NAME}/.env"
echo "APP_NAME=${PACKAGE_NAME}" >> "%{buildroot}/opt/docker-rpm/${PACKAGE_NAME}/.env"

sed -i "s:<PACKAGE_NAME>:${PACKAGE_NAME}:g" "%{buildroot}/etc/systemd/system/${SERVICE_NAME}"

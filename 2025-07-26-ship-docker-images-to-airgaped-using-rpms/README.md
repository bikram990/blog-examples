# Ship Docker images to airgapped systems using rpms

## Usage

- Create RPM

```sh
python create_rpm.py --docker-image "docker.io/library/nginx:1.28.0" --name "nginx" --scripts-dir ./scripts --spec-file image.spec_file --service-file image.service
```

- Install RPM

```sh
sudo rpm --relocate /opt=/test/opt -i docker-to-rpm/RPMS/nginx-1.28.0.rpm
```

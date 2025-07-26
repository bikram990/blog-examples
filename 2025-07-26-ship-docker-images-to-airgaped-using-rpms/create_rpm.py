#!.venv/bin/python

"""create_rpm"""

import os
import sys
from pathlib import Path
import argparse
import shutil
import subprocess
import logging

# https://rpm-software-management.github.io/rpm/manual/spec.html
# https://docs.fedoraproject.org/en-US/packaging-guidelines/RPMMacros/
# more macros can be found using `rpm --showrc`

logger = logging.getLogger(__name__)


def _run_command(command: list[str]):
    logger.info("Executing " + " ".join(command))
    success = False
    try:
        # shell=True means the command will be passed to a shell to execute
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        # proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        # status = proc.wait()
        # stdout, stderr = proc.communicate()
        success = True
    except subprocess.CalledProcessError as e:
        logger.exception("Exception happened")
        output = e.output
    except Exception as e:
        # check_call can raise other exceptions, such as FileNotFoundError
        logger.exception("Exception happened")
        output = str(e)
    logger.debug("output is " + output)
    return success, output


def _login_to_registry(url: str, user: str, password: str):
    status, output = _run_command(
        ["docker", "login", url, "--username", user, "--password", password]
    )
    if not status:
        logger.error(f"Failed to login to docker registry, {output}")
        sys.exit(-1)


def _save_image(name: str, image: str, image_path: str):
    status, output = _run_command(["docker", "image", "inspect", image])
    if not status:
        logger.info(f"{name} Image doesn't exist on the machine, pulling it")
        status, output = _run_command(
            ["docker", "image", "pull", "--platform", "linux/amd64", image]
        )
        if not status:
            logger.error(f"Failed to pull image {name}")
            sys.exit(-1)

    status, output = _run_command(["docker", "image", "save", image, "-o", image_path])
    if not status:
        logger.info(f"Failed to save image {name} as oci-archive {output}")
        sys.exit(-1)


def _create_spec_file(app: dict, build_spec_file: str):
    spec_file: str = app["spec_file"]
    with open(spec_file, mode="r", encoding="utf-8") as src, open(
        build_spec_file, mode="w", encoding="utf-8"
    ) as dest:
        spec_data = src.read()
        if "dependencies" not in app or len(app["dependencies"]) == 0:
            spec_data = spec_data.replace("Requires(pre):  %{?EXTRA_REQUIRES}\n", "")
        dest.write(spec_data)


def _copy_build(app: dict, build_dir: str, image_path: str, image_file_name: str):
    name: str = app["name"]
    service_file: str = app["service_file"]
    prefix: str = f"/opt/docker-rpm/{name}"

    os.makedirs(name=f"{build_dir}/{prefix}", exist_ok=True)
    os.makedirs(name=f"{build_dir}/etc/systemd/system", exist_ok=True)
    shutil.copyfile(src=image_path, dst=f"{build_dir}/{prefix}/{image_file_name}")
    shutil.copyfile(src=service_file, dst=f"{build_dir}/etc/systemd/system/{name}.service")

    additional_sources: str = app.get("additional_sources")

    if additional_sources and len(additional_sources) > 0:
        shutil.copytree(src=additional_sources, dst=build_dir)


def _create_macro_file(app: dict, build_area: str, macro_file_path: str):
    name: str = app["name"]

    image_tag: str = app["image_tag"]
    image_root: str = app["image"]
    image: str = f"{image_root}:{image_tag}"

    image_file_name: str = f"{name}-{image_tag}.tar"
    rpm_name: str = f"{name}-{image_tag}.rpm"

    version: str = app["version"]
    release: str = image_tag
    scripts_dir: str = app["scripts_dir"]

    macro_file = f"""%_topdir {build_area}
%_rpmfilename {rpm_name}
%APP_NAME {name}
%VERSION {version}
%RELEASE_VERSION {release}
%IMAGE_ROOT {image_root}
%IMAGE_TAG {image_tag}
%IMAGE {image}
%TGZ_NAME {image_file_name}
%BUILD_ARCH noarch
%scripts_dir {scripts_dir}
"""
    if "dependencies" in app and len(app["dependencies"]) > 0:
        dependencies = ",".join(app["dependencies"])
        macro_file += f"""%EXTRA_REQUIRES {dependencies}"""

    with open(macro_file_path, mode="w", encoding="utf-8") as f:
        f.write(macro_file)


def _create_agent_rpm(app: dict, temp_dir: str):
    name: str = app["name"]
    build_area: str = f"{temp_dir}/{name}"

    image_tag: str = app["image_tag"]
    image_root: str = app["image"]
    image: str = f"{image_root}:{image_tag}"

    image_file_name: str = f"{name}-{image_tag}.tar"
    rpm_name: str = f"{name}-{image_tag}.rpm"
    image_path: str = f"{build_area}/{image_file_name}"

    os.makedirs(name=build_area, exist_ok=True)
    old_home = os.environ.get("HOME")
    os.environ["HOME"] = build_area
    shutil.rmtree(build_area + "/rpmbuild")
    _run_command(["rpmdev-setuptree"])
    os.environ["HOME"] = old_home

    build_area = build_area + "/rpmbuild"

    if not os.path.exists(path=image_path):
        _save_image(name=name, image=image, image_path=image_path)

    macro_file_path = f"{build_area}/../.rpmmacros"
    _create_macro_file(app=app, build_area=build_area, macro_file_path=macro_file_path)

    build_dir = f"{build_area}/BUILD"
    _copy_build(
        app=app, build_dir=build_dir, image_path=image_path, image_file_name=image_file_name
    )

    build_spec_file = f"{build_area}/SPECS/docker-to-rpm.spec"
    _create_spec_file(app=app, build_spec_file=build_spec_file)

    include_file_macro = Path(__file__).parent.resolve() / "include-file.macro"

    status, output = _run_command(
        [
            "rpmbuild",
            f"--load={macro_file_path}",
            f"--load={include_file_macro}",
            "-bb",  # Binary package
            # "-bs",  # Source package
            build_spec_file,
        ]
    )
    if not status:
        logger.error(f"Failed to create rpm with error {output}")
        sys.exit(-1)

    rpms_file = f"{build_area}/RPMS/{rpm_name}"
    os.makedirs(f"{temp_dir}/RPMS", exist_ok=True)
    shutil.move(src=rpms_file, dst=f"{temp_dir}/RPMS/{rpm_name}")


def main():
    """main"""
    args = _parse_args()
    _init_logging(args=args)
    temp_location = os.path.abspath("./docker-to-rpm")
    if not os.path.exists(temp_location):
        os.mkdir(temp_location)

    if args.docker_username and args.docker_password:
        _login_to_registry(
            url=args.docker_registry, user=args.docker_username, password=args.docker_password
        )

    image, tag = args.docker_image.split(sep=":", maxsplit=1)

    app = {
        "name": args.name,
        "version": tag,
        "image": image,
        "image_tag": tag,
        "service_file": os.path.abspath(args.service_file),
        "spec_file": os.path.abspath(args.spec_file),
        "additional_sources": args.additional_sources_dir,
        "scripts_dir": args.scripts_dir,
    }
    logger.info(f"Processing app: {app['name']}")
    _create_agent_rpm(app=app, temp_dir=temp_location)


def _init_logging(args):
    """_init_logging"""

    LOG_LEVELS = ["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]
    log_level_name = LOG_LEVELS[min(len(LOG_LEVELS) - 1, args.verbose)]
    logging.basicConfig(format="%(levelname)s: %(message)s", level=log_level_name)


def _parse_args():
    """_parse_args"""
    parser = argparse.ArgumentParser(description="Docker to RPM", add_help=True)
    parser.add_argument("--version", action="version", version="%(prog)s 1.0")
    parser.add_argument("--verbose", "-v", action="count", default=4)

    parser.add_argument(
        "--docker-registry",
        default="registry-1.docker.io",
        type=str,
        help="Docker registry to login",
    )
    parser.add_argument("--docker-username", type=str, help="Username for Docker registry")
    parser.add_argument("--docker-password", type=str, help="Password for Docker registry")

    parser.add_argument(
        "--docker-image", type=str, required=True, help="Docker image to package inside RPM"
    )
    parser.add_argument("--name", type=str, required=True, help="Name of the RPM package")
    parser.add_argument(
        "--description",
        default="Docker image packaged as a RPM",
        type=str,
        help="RPM package description",
    )
    parser.add_argument("--service-file", type=str, required=True, help="Path to service file")
    parser.add_argument("--spec-file", type=str, required=True, help="Path to spec file")
    parser.add_argument("--scripts-dir", type=_valid_dir, required=True, help="Path to scripts dir")
    parser.add_argument(
        "--additional-sources-dir",
        type=_valid_dir,
        help="Any additional files which you want to ship in RPM / access in scripts",
    )
    parser.add_argument(
        "--dependencies",
        type=str,
        help="Comma separate list of RPM dependencies",
    )

    parser.add_argument("--output", type=str, help="Output RPM file")

    return parser.parse_args()


def _valid_dir(path):
    if not os.path.exists(path) or os.path.isfile(path):
        msg = f"not a valid dir: {path}"
        raise argparse.ArgumentTypeError(msg)
    return os.path.abspath(path)


if __name__ == "__main__":
    main()

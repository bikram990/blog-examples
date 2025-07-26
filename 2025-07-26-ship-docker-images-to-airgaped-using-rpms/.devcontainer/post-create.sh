#!/usr/bin/zsh

git_setup() {
    git config --global --add safe.directory "${DEVCONTAINER_WORKSPACE_PATH}"
    git config --global pull.rebase true
    git config --global --add --bool push.autoSetupRemote true
}

python_setup() {
    (echo '# Add user python packages bin to PATH'; echo 'export PATH="$HOME/.local/bin:$PATH"') >> ~/.zshrc
    export PATH="$HOME/.local/bin:$PATH"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    rm -Rf .venv
    uv venv
    (echo '# Activate the python env'; echo ". ${DEVCONTAINER_WORKSPACE_PATH}/.venv/bin/activate") >> ~/.zshrc
}

app_setup() {
    export PATH="$HOME/.local/bin:$PATH"
    . .venv/bin/activate
    uv pip install pylint
}

container_setup() {
    echo "Setting up the container"
    git_setup &
    python_setup &

    wait

    app_setup
}

usage() {
    echo "$0 <action>"
    echo "$1 is invalid action"
    echo "valid actions setup, dep, python"
    echo "setup will run all the steps run at dev container creation"
    echo "dep will install python dependencies"
    echo "python will recreate the python venv and install python dependencies"
    exit 64
}

action=$1

case $action in
  dep)
    . .venv/bin/activate
    app_setup
    ;;
  python)
    python_setup
    . .venv/bin/activate
    app_setup
    ;;
  help)
    usage $action
    ;;
  *)
    container_setup
    ;;
esac

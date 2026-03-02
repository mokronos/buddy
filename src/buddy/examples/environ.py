import docker
from docker.errors import ImageNotFound, NotFound
from docker.models.containers import Container

DOCKERFILE = "./src/buddy/environment/docker/Dockerfile"
IMAGE = "environ"
TAG = "latest"
CONTAINER_NAME = "environ-example"
COMMAND = "ls /"
KEEPALIVE_COMMAND = ["sh", "-lc", "while true; do sleep 3600; done"]

client = docker.from_env()


def ensure_image_exists(image_ref: str) -> None:
    try:
        client.images.get(image_ref)
    except ImageNotFound as error:
        raise RuntimeError(
            f"Docker image '{image_ref}' is not built yet. Build it first using {DOCKERFILE}."
        ) from error


def get_or_start_container(image_ref: str) -> Container:
    def create_container() -> Container:
        return client.containers.run(
            image_ref,
            detach=True,
            name=CONTAINER_NAME,
            command=KEEPALIVE_COMMAND,
        )

    try:
        container = client.containers.get(CONTAINER_NAME)
        container.reload()
        current_cmd = container.attrs.get("Config", {}).get("Cmd") or []
        if current_cmd != KEEPALIVE_COMMAND:
            container.remove(force=True)
            return create_container()
        if container.status != "running":
            container.start()
            container.reload()
        if container.status != "running":
            container.remove(force=True)
            return create_container()
        return container
    except NotFound:
        return create_container()


def run_command(container: Container, command: str) -> str:
    result = container.exec_run(["sh", "-lc", command])
    if result.exit_code != 0:
        output = result.output.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Command failed ({result.exit_code}): {output}")
    return result.output.decode("utf-8", errors="replace").strip()


image_ref = f"{IMAGE}:{TAG}"
ensure_image_exists(image_ref)
container = get_or_start_container(image_ref)
output = run_command(container, COMMAND)

print(f"container={container.name} image={image_ref}")
print(f"command={COMMAND}")
print(output)

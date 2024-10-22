import json
import logging
from pathlib import Path
import signal
from typing import List, Union
from pydantic import BaseModel, Field
REFRESH = False

logger = logging.getLogger(__name__)
level = logging.INFO
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
formatter = logging.Formatter('[%(levelname)s] - %(message)s (%(lineno)d)')
ch.setFormatter(formatter)
logger.addHandler(ch)

def timed_input(prompt="", timeout=5, timeout_msg=""):
    def timeout_error(*_):
        raise TimeoutError

    signal.signal(signal.SIGALRM, timeout_error)
    signal.alarm(timeout)
    try:
        response = input(prompt)
        signal.alarm(0)
        return response
    except TimeoutError:
        if timeout_msg:
            logger.info(timeout_msg)
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        return None

class Asset(BaseModel):
    name: str = Field(default_factory=str)
    path: str = Field(default_factory=str)
    bundle_name: str = Field(default_factory=str)
    x: float = Field(default_factory=float)
    y: float= Field(default_factory=float)
    z: float= Field(default_factory=float)


class AssetBundle(BaseModel):
    name: str = Field(default_factory=str)
    assets: List[Asset] = Field(default=[])
    
    class Config:
        arbitrary_types_allowed = True

def read_bundle(fname: Union[Path, str]) -> AssetBundle:
    assets:List[Asset] = []
    with open(fname, "r") as file:
        for line in file:
            asset_data = line.rstrip("\n").split(",")
            data = {
                "name": asset_data[0],
                "path": asset_data[1],
                "bundle_name": asset_data[2],
                "x": float(asset_data[3]),
                "y": float(asset_data[4]),
                "z": float(asset_data[5]),
            }
            assets.append(Asset(**data))
    bundle_names = set(asset.bundle_name for asset in assets)
    assert len(bundle_names) == 1, f"{csv_file} contains multiple asset bundles"
    bundle_name = bundle_names.pop()
    return AssetBundle(name=bundle_name, assets=assets)


def write_bundle_info(bundle: AssetBundle, fname_json: Union[Path, str]):
    bundle_info = {asset.name: asset.path for asset in bundle.assets}
    with open(fname_json, "w") as f:
        json.dump(bundle_info, f, indent=4)
    logger.info(
        f'Populate bundle info class in "config_writer.py" using "{fname_json}"'
    )


def snake2camel(snake_string: str) -> str:
    return snake_string.title().replace("_", "")


def write_model_scenic(bundle, fname_model="model.scenic"):
    fname_model.parent.mkdir(parents=False, exist_ok=True)
    with open(fname_model, "w") as f:
        for i, asset in enumerate(bundle.assets):
            lines = [
                f"class {snake2camel(asset.name)}:\n",
                f"    width: {asset.x}\n",  # x
                f"    length: {asset.z}\n",  # z
                f"    height: {asset.y}\n",  # y
                f'    asset_name = "{asset.name}"\n',
                f'    asset_bundle = "{asset.bundle_name}"\n',
                f'    asset_path = "{asset.path}"\n',
            ]
            if i > 0:
                lines = ["\n\n"] + lines
            f.writelines(lines)


def process_bundle(bundle: AssetBundle, path: Path):
    fname_model = path / f"{bundle.name}_model.scenic"
    fname_json = path / f"{bundle.name}_info.json"
    logger.info(f"Storing model in {fname_model}")
    logger.info(f"Storing bundle info in {fname_json}")
    if fname_model.exists():
        if not REFRESH:
            response = timed_input(
                f'Scenic file for "{bundle.name}" already exists. Replace? [Y/n] '
            )
            replace = response in ["", "y", "Y", "yes", "Yes"]
        if REFRESH or replace:
            logger.info(f'Replacing existing "{bundle.name}" Scenic model file')
        else:
            logger.info(f'\nModel file exists, skipping "{bundle.name}" bundle')
            return
    write_bundle_info(bundle, fname_json)
    write_model_scenic(bundle, fname_model)


if __name__ == "__main__":
    csv_files = Path(Path(__file__).parent).rglob("*.csv")
    print(csv_files)
    for csv_file in csv_files:
        bundle = read_bundle(csv_file)
        logger.info(f'Processing "{bundle.name}" bundle from "{csv_file}"')
        process_bundle(bundle=bundle,path = Path(__file__).parent)

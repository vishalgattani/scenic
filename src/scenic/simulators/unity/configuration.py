from datetime import datetime
import json
import logging
import os
import pathlib
from typing import List
from pydantic import BaseModel, Field, model_validator, computed_field
import numpy as np
import pandas as pd
from scipy.spatial.transform import Rotation as R


logger = logging.getLogger(__name__)
level = logging.DEBUG
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
formatter = logging.Formatter('[%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)')
ch.setFormatter(formatter)
logger.addHandler(ch)

__asset_info_columns__ = ("name", "path", "bundle", "width", "height", "length")
__cwd__ = pathlib.Path(os.path.abspath(__file__)).parent


class Info(BaseModel):
    """Generic JSON 'info' class.

    Attributes:
        name (str): The name of one of the assets within the asset bundle.
        full_name (str): The full name, with path, of the asset within the asset bundle.
        asset_bundle (str): The name of the asset bundle.
    """

    name: str
    full_name: str = Field(default=None)
    asset_bundle: str = Field(default=None)


class InfoRobots(Info):
    """JSON 'info' class for the "vehicles" asset bundle.

    Attributes:
        name (str): The name of one of the assets within the "vehicles" asset bundle.
        full_name (str): The full name, with path, of the asset within the "vehicles" asset bundle.
        asset_bundle (str): The name of the asset bundle: "vehicles"
    """
    asset_bundle: str = Field(default="robot.bytes")
    full_name: str = Field(default=None)
    @model_validator(mode="after")
    def validate_model(cls, values):
        asset_bundle = values.asset_bundle
        name = values.name
        asset_info_csv = __cwd__ / f"new_bundles/{asset_bundle}_asset_info.csv"
        try:
            df = pd.read_csv(asset_info_csv, header=None, names=__asset_info_columns__)
            key_value_pairs = dict(zip(df["name"].apply(lambda x:x.lower()), df["path"]))
            if name not in key_value_pairs:
                raise KeyError(f'The "{asset_bundle}" asset bundle does not include "{name}".')
            values.full_name = key_value_pairs[name]
        except FileNotFoundError:
            logger.error(f"Asset info CSV file not found: {asset_info_csv}")
            raise
        except KeyError as e:
            logger.error(str(e))
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred: {str(e)}")
            raise
        return values


class ThreeVector(BaseModel):
    x: float
    y: float
    z: float
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {
            np.ndarray: lambda v: v.tolist()  # Convert ndarray to list for JSON serialization
        }

    @computed_field
    @property
    def array(self) -> np.ndarray:
        return np.array([self.x, self.y, self.z])

class Normalized(ThreeVector):
    magnitude: float = Field(default=None)
    sqr_magnitude: float = Field(default=None)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        sqr_magnitude = self.array.dot(self.array)
        self.magnitude = float(np.sqrt(sqr_magnitude))
        self.sqr_magnitude = float(sqr_magnitude)

class SuperVector(Normalized):
    normalized: ThreeVector = Field(default=None,exclude=True)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        if 0 < self.magnitude:
            norm = self.array / self.magnitude
            self.normalized = Normalized(x=norm[0], y=norm[1], z=norm[2])
        else:
            logger.warning("Skipping normalization of zero magnitude vector.")
            self.normalized = Normalized(x=self.x, y=self.y, z=self.z)

class Position(SuperVector):
    pass

class Rotation(BaseModel):
    euler_angles: SuperVector
    x: float = Field(default=None)
    y: float = Field(default=None)
    z: float = Field(default=None)
    w: float = Field(default=None)

    def model_post_init(self, __context) -> None:
        super().model_post_init(__context)
        r = R.from_euler("yxz", self.euler_angles.array, degrees=True)
        self.y, self.x, self.z, self.w = r.as_quat()

    class Config:
        arbitrary_types_allowed = True


class Obstacle(BaseModel):
    info: Info = Field(exclude=False)
    name: str = Field(exclude=False)
    position: Position = Field(exclude=False)
    rotation: Rotation = Field(exclude=False)
    scale: SuperVector = Field(exclude=False)
    
    class Config:
        arbitrary_types_allowed = True



class Configuration(BaseModel):
    obstacles: List[Obstacle]
    class Config:
        arbitrary_types_allowed = True
    def to_json(self, fname, pretty=False) -> str:
        indent = 4 if pretty else None
        with open(fname, "w") as f:
            json.dump(
                [obstacle.to_dict() for obstacle in self.obstacles], f, indent=indent
            )


if __name__ == "__main__":
    obstacles = []
    name_1 = "husky"
    info_1 = InfoRobots(name=name_1.lower())
    position_1 = Position(x=0.0490000844, y=0.140999854, z=-30.276001)
    euler_angles_1 = SuperVector(x=0, y=165.55, z=0)
    rotation_1 = Rotation(euler_angles=euler_angles_1)
    scale_1 = SuperVector(x=1.0, y=1.0, z=1.0)
    obstacles.append(Obstacle(info=info_1, name=name_1, position=position_1, rotation=rotation_1, scale=scale_1))
    configuration = Configuration(obstacles=obstacles)
    logger.debug(f"Generated configuration: {configuration}")
    # today = datetime.now().strftime("%Y%m%d")
    # fname = pathlib.Path(f"config_samples/{today}-mixed-obstacles.json")
    # fname.parent.mkdir(parents=True, exist_ok=True)
    # barricade.to_json(fname, pretty=True)
    logger.info(configuration.model_dump_json(indent=2))

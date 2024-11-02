import logging
from pathlib import Path
from typing import Union,Optional, List
import numpy as np
from datetime import datetime
from scenic.simulators.unity import configuration
import scenic.syntax.translator as translator

logger = logging.getLogger(__name__)
level = logging.INFO
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
logger.addHandler(ch)


def save_scene(scene, fname, show=False):
    import matplotlib.pyplot as plt

    ax_i = plt.gca()
    ax_i.set_aspect("equal")
    scene.workspace.show2D(plt)
    min_x = min_y = np.inf
    max_x = max_y = -np.inf
    for obj in scene.objects:
        min_x = min(obj.position[0], min_x)
        min_y = min(obj.position[1], min_y)
        max_x = max(obj.position[0], max_x)
        max_y = max(obj.position[1], max_y)

        obj.show2D(scene.workspace, plt, highlight=(obj is scene.egoObject))
        plt.annotate(obj.asset_name, obj.position[:2])

    ax_i.set_xlim(min_x - 1, max_x + 1)
    ax_i.set_ylim(min_y - 1, max_y + 1)

    plt.savefig(fname.with_suffix(".png"), dpi=400)
    if show:
        plt.show()
    plt.clf()


def main(fname_scenic:Union[str,Path], path:Optional[Union[str,Path]]=None, n_scenes:int=1, show:bool=False, obstacle_height:float=100)->List[Path]:
    assert Path(fname_scenic).exists(), f"no such file: {fname_scenic}"
    # setup the scenario inputs
    params = {}  # global parameters to override
    model = None  # specific Scenic world model
    specific_scenario = None  # name of scenario scene to run (if file contains multiple)

    # instantiate the scenario object
    scenario = translator.scenarioFromFile(
        str(fname_scenic),
        params=params,
        model=model,
        scenario=specific_scenario,
    )

    fnames = []
    run_time = datetime.now().strftime("%Y%m%d-%H-%M-%S")
    for i in range(n_scenes):
        logger.info(f"Generating scene {i+1} of {n_scenes}...")

        # generate a single scene from the scenario
        scene, _ = scenario.generate(verbosity=1)  # verbosity >= 1 shows more detail

        obstacles = []
        for obj in scene.objects:
            # get object positions and orientations
            heading = np.degrees(obj.heading)
            logger.debug(f"{obj.asset_name}, heading: rad={obj.heading}, deg={heading}")
            # if obj is scene.egoObject:
            #     continue  # this removes the 1st vehicle from the configuration, should be ego
            # else:
            info = configuration.get_asset_info(asset_name=obj.asset_name)
            logger.info(f"info: {info}")
            obstacles.append(
                configuration.Obstacle(
                    info=info,
                    name=obj.asset_name,
                    position=configuration.Position(
                        x=obj.position[0], y=obstacle_height, z=obj.position[1]
                    ),
                    rotation=configuration.Rotation(euler_angles=configuration.SuperVector(x=0, y=-heading, z=0)),
                    scale=configuration.SuperVector(x=1.0, y=1.0, z=1.0),
                )
            )

            configuration_i = configuration.Configuration(obstacles=obstacles)

        # write configuration to a file
        fname = f"{run_time}-scene-{i}.json"
        if path is None:
            fname = Path(fname_scenic.parent) / fname
        else:
            fname = Path(path) / fname
        fname.parent.mkdir(parents=True, exist_ok=True)
        with open(fname, "w") as f:
            f.write(configuration_i.model_dump_json(indent=2))
        logger.info(f'scene saved to "{fname}"')
        fnames.append(fname)
        save_scene(scene, fname, show=show)
    return fnames


if __name__ == "__main__":
    fname_scenic = Path(__file__).parent/"demo.scenic"
    main(fname_scenic)

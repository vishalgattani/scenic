import logging
import pathlib
from scenic.simulators.unity.configuration import Info, InfoBundle, Obstacle, Configuration, Position, Rotation, SuperVector
import scenic.syntax.translator as translator
import numpy as np
import matplotlib.pyplot as plt
import json 
logger = logging.getLogger(__name__)
level = logging.INFO
logger.setLevel(level)
ch = logging.StreamHandler()
ch.setLevel(level)
logger.addHandler(ch)
logging.getLogger("matplotlib").setLevel(logging.WARNING)


def save_scene(scene, fname, show=False):
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



def main(fname_scenic, path=None, n=1, show=False, obstacle_height=100):
    assert pathlib.Path(fname_scenic).exists(), f"no such file: {fname_scenic}"

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
    for i in range(n):
        logger.info(f"Generating scene {i+1} of {n}...")

        # generate a single scene from the scenario
        scene, _ = scenario.generate(verbosity=1)  # verbosity >= 1 shows more detail

        obstacles = []
        for obj in scene.objects:
            # get object positions and orientations
            heading = np.degrees(obj.heading)
            logger.debug(f"{obj.asset_name}, heading: rad={obj.heading}, deg={heading}")
            if obj is scene.egoObject:
                continue  # this removes the 1st vehicle from the configuration, should be ego
            elif obj.asset_name in ["Husky", "Warthog", "Quadrotor", "Quadrotor_px4"]:
                info = InfoBundle(name=obj.asset_name, asset_bundle="robot.bytes")
            else:
                for bundle in ["barrierpack.bytes", "grass.bytes", "rocks.bytes"]:
                    try:
                        info = InfoBundle(name=obj.asset_name, asset_bundle=bundle)
                        break
                    except KeyError:
                        continue
            obstacles.append(
                Obstacle(
                    info=info,
                    name=obj.asset_name,
                    position=Position(
                        x=obj.position[0], y=obstacle_height, z=obj.position[1]
                    ),
                    rotation=Rotation(euler_angles=SuperVector(x=0, y=-heading, z=0)),
                    scale=SuperVector(x=1.0, y=1.0, z=1.0),
                )
            )

            configuration_i = Configuration(obstacles=obstacles)

        # write configuration to a file
        if n > 1:
            fname = f"{fname_scenic.stem}_{i:02d}.json"
        else:
            fname = f"{fname_scenic.stem}.json"
        if path is None:
            fname = pathlib.Path(fname_scenic.parent) / fname
        else:
            fname = pathlib.Path(path) / fname
        fname.parent.mkdir(parents=True, exist_ok=True)
        with open(fname, "w") as f:
            json.dump(configuration_i.model_dump(), f, indent=4)
        # configuration_i.model_dump_json(indent=2)
        logger.info(f'scene saved to "{fname}"')
        fnames.append(fname)

        save_scene(scene, fname, show=show)

    return fnames

if __name__ == "__main__":
    try:
        # scenic_fname = pathlib.Path("demo.scenic")
        scenic_fname = pathlib.Path("demo.scenic")
        assert scenic_fname.exists(), f"no such file: {scenic_fname}"
        # scenic_fname = pathlib.Path("husky_follow_the_leader.scenic")
        main(scenic_fname, path="demo_scene", obstacle_height=0.5, show=False)
    except AssertionError as e:
        logger.error(e)
    except Exception as e:
        logger.error(f"Unexpected error occurred: {str(e)}")
        logger.exception(e)

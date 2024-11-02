from scenic.simulators.unity.barrierpack.model import Barrier, TrafficBarrel, DelineatorTubeOrange
from scenic.simulators.unity.robot.model import Warthog

ego = new Warthog at 0.0 @ 0.0
bottleneck = new OrientedPoint offset by Range(-1.5, 1.5) @ Range(2, 3), facing Range(-30.0, 30.0) deg
goal = new TrafficBarrel beyond bottleneck by Range(-0.5, 0.5) @ 6

require abs((angle to goal) - (angle to bottleneck)) <= 10 deg

gap = 2 * ego.width
half_gap = gap / 2
left_edge = new OrientedPoint at bottleneck offset by -half_gap @ 0,
    facing Range(60,120) deg relative to bottleneck.heading
right_edge = new OrientedPoint at bottleneck offset by half_gap @ 0,
    facing Range(240,300) deg relative to bottleneck.heading
new Barrier ahead of left_edge
new Barrier ahead of right_edge

new DelineatorTubeOrange beyond bottleneck by Range(1, 3) @ Range(1, 1.5)
new DelineatorTubeOrange beyond bottleneck by Range(-4, -2) @ Range(1.5, 2)
new DelineatorTubeOrange beyond bottleneck by Range(-1, 1) @ Range(2,2.5)
new DelineatorTubeOrange beyond bottleneck by Range(2, 4) @ Range(2.5, 3)
new DelineatorTubeOrange beyond bottleneck by Range(-2, 0) @ Range(3, 3.5)
new DelineatorTubeOrange beyond bottleneck by Range(-4, -2) @ Range(3.5, 4)
new DelineatorTubeOrange beyond bottleneck by Range(-1, 1) @ Range(4, 4.5)
new DelineatorTubeOrange beyond bottleneck by Range(2, 4) @ Range(4.5, 5)

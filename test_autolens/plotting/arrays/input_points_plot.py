from autoarray import scaled_array
from autolens.plotters import array_plotters
import numpy as np

array = aa.Scaled(sub_array_1d=np.ones((50, 50)), pixel_scales=0.1)

# array_plotters.plot_array(array=array, centres=[[(1.0, 1.0)], [(-1.0, 1.0)], [(-2.0, -2.0), (-3.0, -3.0)]])
array_plotters.plot_array(
    array=array, centres=[[(0.0, 0.0)]], axis_ratios=[[0.5]], phis=[[45.0]]
)
stop
array_plotters.plot_array(
    array=array,
    centres=[[(0.0, 0.0)], [(-1.0, 1.0)], [(-2.0, -2.0), (-3.0, -3.0)]],
    axis_ratios=[[0.5], [0.5], [0.3, 0.3]],
    phis=[[0.0], [90.0], [45.0, 15.0]],
)
array_plotters.plot_array(
    array=array, positions=[[[1.0, 1.0], [2.0, 2.0]], [[-1.0, -1.0]]]
)

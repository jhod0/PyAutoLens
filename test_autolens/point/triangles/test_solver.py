import numpy as np
import pytest

import autolens as al
import autogalaxy as ag
from autolens.point.triangles.triangle_solver import TriangleSolver


@pytest.fixture
def solver():
    tracer = al.Tracer(
        galaxies=[
            al.Galaxy(
                redshift=0.5,
                mass=ag.mp.Isothermal(
                    centre=(2.0, 1.0),
                    einstein_radius=1.0,
                ),
            )
        ]
    )
    grid = al.Grid2D.uniform(
        shape_native=(100, 100),
        pixel_scales=0.05,
    )

    return TriangleSolver(
        tracer=tracer,
        grid=grid,
        target_pixel_scale=0.01,
    )


def test_solver(solver):
    assert solver.solve(
        source_plane_coordinate=(0.0, 0.0),
    )


def test_steps(solver):
    assert solver.n_steps == 3


class NullTracer(al.Tracer):
    def __init__(self):
        super().__init__([])

    def deflections_yx_2d_from(self, grid):
        return np.zeros_like(grid)


def test_trivial():
    solver = TriangleSolver(
        tracer=NullTracer(),
        grid=al.Grid2D.uniform(
            shape_native=(100, 100),
            pixel_scales=0.05,
        ),
        target_pixel_scale=0.01,
    )
    (coordinates,) = solver.solve(
        source_plane_coordinate=(0.0, 0.0),
    )
    assert coordinates == pytest.approx((0.0, 0.0), abs=1.0e-3)

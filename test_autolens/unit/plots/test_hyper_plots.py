import autolens as al
import os

import pytest


@pytest.fixture(name="hyper_plotter_path")
def make_hyper_plotter_setup():
    return "{}/../../test_files/plotting/hyper_galaxies/".format(
        os.path.dirname(os.path.realpath(__file__))
    )


def test__plot_individual_images(
    hyper_model_image_7x7,
    hyper_galaxy_image_0_7x7,
    contribution_map_7x7,
    hyper_noise_map_7x7,
    masked_imaging_fit_x1_plane_7x7,
    hyper_plotter_path,
    plot_patch,
):

    al.plot.hyper.hyper_galaxy_image(
        galaxy_image=hyper_galaxy_image_0_7x7,
        array_plotter=al.plotter.array(
            output=al.plotter.Output(path=hyper_plotter_path, format="png")
        ),
    )

    assert hyper_plotter_path + "hyper_galaxy_image.png" in plot_patch.paths

def test__plot_subplot_of_hyper_galaxy(
    hyper_galaxy_image_0_7x7,
    contribution_map_7x7,
    noise_map_7x7,
    hyper_noise_map_7x7,
    masked_imaging_fit_x2_plane_7x7,
    hyper_plotter_path,
    plot_patch,
):
    al.plot.hyper.subplot_of_hyper_galaxy(
        fit=masked_imaging_fit_x2_plane_7x7,
        hyper_fit=masked_imaging_fit_x2_plane_7x7,
        galaxy_image=hyper_galaxy_image_0_7x7,
        array_plotter=al.plotter.array(
            output=al.plotter.Output(path=hyper_plotter_path, format="png")
        ),
    )

    assert hyper_plotter_path + "hyper_galaxies.png" in plot_patch.paths


def test__plot_hyper_galaxy_images(
    hyper_galaxy_image_0_7x7,
    hyper_galaxy_image_1_7x7,
    mask_7x7,
    hyper_plotter_path,
    plot_patch,
):
    hyper_galaxy_image_path_dict = {}

    hyper_galaxy_image_path_dict[("g0",)] = hyper_galaxy_image_0_7x7
    hyper_galaxy_image_path_dict[("g1",)] = hyper_galaxy_image_1_7x7

    al.plot.hyper.subplot_of_hyper_galaxy_images(
        hyper_galaxy_image_path_dict=hyper_galaxy_image_path_dict,
        mask=mask_7x7,
        array_plotter=al.plotter.array(
            output=al.plotter.Output(path=hyper_plotter_path, format="png")
        ),
    )

    assert hyper_plotter_path + "hyper_galaxy_images.png" in plot_patch.paths

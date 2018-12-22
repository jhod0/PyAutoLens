import os

from autofit import conf
from autofit.core import non_linear as nl
from autolens.model.galaxy import galaxy, galaxy_model as gm
from autolens.pipeline import phase as ph
from autolens.pipeline import pipeline as pl
from autolens.model.profiles import light_profiles as lp, mass_profiles as mp
from test.integration import tools

test_type = 'lens_and_source'
test_name = "lens_both_x1_source_x1"

path = '{}/../../'.format(os.path.dirname(os.path.realpath(__file__)))
output_path = path+'output/'+test_type
config_path = path+'config'
conf.instance = conf.Config(config_path=config_path, output_path=output_path)

def pipeline():


    lens_light = lp.SphericalDevVaucouleurs(centre=(0.0, 0.0), intensity=0.1, effective_radius=0.5)
    lens_mass = mp.EllipticalIsothermal(centre=(0.0, 0.0), axis_ratio=0.8, phi=80.0, einstein_radius=1.6)
    source_light = lp.EllipticalSersic(centre=(0.0, 0.0), axis_ratio=0.6, phi=90.0, intensity=1.0,
                                       effective_radius=0.5, sersic_index=1.0)

    lens_galaxy = galaxy.Galaxy(dev=lens_light, sie=lens_mass)
    source_galaxy = galaxy.Galaxy(sersic=source_light)

    tools.reset_paths(test_name=test_name, output_path=output_path)
    tools.simulate_integration_image(test_name=test_name, pixel_scale=0.1, lens_galaxies=[lens_galaxy],
                                     source_galaxies=[source_galaxy], target_signal_to_noise=30.0)
    image = tools.load_image(test_name=test_name, pixel_scale=0.1)

    pipeline = make_pipeline(test_name=test_name)
    pipeline.run(image=image)


def make_pipeline(test_name):

    phase1 = ph.LensSourcePlanePhase(lens_galaxies=[gm.GalaxyModel(dev=lp.SphericalDevVaucouleurs,
                                                                   sie=mp.EllipticalIsothermal)],
                                     source_galaxies=[gm.GalaxyModel(sersic=lp.EllipticalSersic)],
                                     optimizer_class=nl.MultiNest, phase_name="{}/phase1".format(test_name))

    phase1.optimizer.n_live_points = 60
    phase1.optimizer.sampling_efficiency = 0.8

    return pl.PipelineImaging(test_name, phase1)


if __name__ == "__main__":
    pipeline()

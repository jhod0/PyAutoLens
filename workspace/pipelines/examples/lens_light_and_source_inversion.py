from autofit.optimize import non_linear as nl
from autofit.mapper import model_mapper as mm
from autolens.data.array import mask as msk
from autolens.model.galaxy import galaxy_model as gm
from autolens.pipeline import phase as ph
from autolens.pipeline import pipeline
from autolens.model.profiles import light_profiles as lp
from autolens.model.profiles import mass_profiles as mp
from autolens.model.inversion import pixelizations as pix
from autolens.model.inversion import regularization as reg

# In this pipeline, we'll perform a basic analysis which initializes a lens model (the lens's light, mass and source's \
# light) and then fits the source galaxy using an inversion. This pipeline will use four phases:

# Phase 1) Fit the lens galaxy's light using an elliptical Sersic light profile.

# Phase 2) Use this lens subtracted image to fit the lens galaxy's mass (SIE+Shear) and source galaxy's light (Sersic).

# Phase 4) Initialize the resolution and regularization coefficient of the inversion using the best-fit lens model from
#          phases 1 and 2.

# Phase 5) Refit the lens galaxy's light and mass models using an inversion, with lens galaxy priors initialized from
#          phases 1 and 2 and source-pixelization parameters from phase 3.

# The first 3 phases of this pipeline are identical to the 'lens_light_and_x1_source_parametric.py' pipeline.

def make_pipeline(pipeline_path=''):

    pipeline_name = 'pipeline_light_and_source_inversion'
    pipeline_path = pipeline_path + pipeline_name

    # We will switch between a circular mask which includes the lens light and an annular mask which removes it.

    def mask_function_circular(image):
        return msk.Mask.circular(shape=image.shape, pixel_scale=image.pixel_scale, radius_arcsec=3.0)

    def mask_function_annular(image):
        return msk.Mask.circular_annular(shape=image.shape, pixel_scale=image.pixel_scale,
                                         inner_radius_arcsec=0.3, outer_radius_arcsec=3.0)

    ### PHASE 1 ###

    # In phase 1, we will fit only the lens galaxy's light, where we:

    # 1) Set our priors on the lens galaxy (y,x) centre such that we assume the image is centred around the lens galaxy.
    # 2) Use a circular mask which includes the lens and source galaxy light.

    class LensPhase(ph.LensPlanePhase):

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.light.centre_0 = mm.GaussianPrior(mean=0.0, sigma=0.1)
            self.lens_galaxies.lens.light.centre_1 = mm.GaussianPrior(mean=0.0, sigma=0.1)

    phase1 = LensPhase(lens_galaxies=dict(lens=gm.GalaxyModel(light=lp.EllipticalSersic)),
                       optimizer_class=nl.MultiNest, mask_function=mask_function_circular,
                       phase_name=pipeline_path + '/phase_1_lens_light_only')

    # You'll see these lines throughout all of the example pipelines. They are used to make MultiNest sample the \
    # non-linear parameter space faster (if you haven't already, checkout the tutorial '' in howtolens/chapter_2).

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 30
    phase1.optimizer.sampling_efficiency = 0.3

    ### PHASE 2 ###

    # In phase 2, we will fit the lens galaxy's mass and source galaxy's light, where we:

    # 1) Use a lens-subtracted image generated by subtracting model lens galaxy image from phase 1.
    # 2) Use a circular annular mask which includes only the source-galaxy light.
    # 3) Initialize the priors on the centre of the lens galaxy's mass-profile by linking them to those inferred for \
    #    its light profile in phase 1.

    class LensSubtractedPhase(ph.LensSourcePlanePhase):

        def modify_image(self, image, previous_results):
            return image - previous_results[0].unmasked_lens_plane_model_image

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.mass.centre_0 = previous_results[0].variable.lens.light.centre_0
            self.lens_galaxies.lens.mass.centre_1 = previous_results[0].variable.lens.light.centre_1

    phase2 = LensSubtractedPhase(lens_galaxies=dict(lens=gm.GalaxyModel(mass=mp.EllipticalIsothermal,
                                                                        shear=mp.ExternalShear)),
                                 source_galaxies=dict(source=gm.GalaxyModel(light=lp.EllipticalSersic)),
                                 optimizer_class=nl.MultiNest, mask_function=mask_function_annular,
                                 phase_name=pipeline_path + '/phase_2_source_only')

    phase2.optimizer.const_efficiency_mode = True
    phase2.optimizer.n_live_points = 60
    phase2.optimizer.sampling_efficiency = 0.2


    ### PHASE 3 ###

    # In phase 3, we will fit simultaneously the lens and source galaxies, where we:

    # 1) Initialize the lens's light, mass, shear and source's light using the results of phases 1 and 2.

    class LensSourcePhase(ph.LensSourcePlanePhase):

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.light = previous_results[0].variable.lens.light
            self.lens_galaxies.lens.mass = previous_results[1].variable.lens.mass
            self.lens_galaxies.lens.shear = previous_results[1].variable.lens.shear
            self.source_galaxies.source = previous_results[1].variable.source

    phase3 = LensSourcePhase(lens_galaxies=dict(lens=gm.GalaxyModel(light=lp.EllipticalSersic,
                                                                    mass=mp.EllipticalIsothermal,
                                                                    shear=mp.ExternalShear)),
                             source_galaxies=dict(source=gm.GalaxyModel(light=lp.EllipticalSersic)),
                             optimizer_class=nl.MultiNest, phase_name=pipeline_path + '/phase_3_both')

    phase3.optimizer.const_efficiency_mode = True
    phase3.optimizer.n_live_points = 75
    phase3.optimizer.sampling_efficiency = 0.3

    ### PHASE 4 ###

    # In phase 4, we initialize the inversion's resolution and regularization coefficient, where we:

    # 1) Use a lens-subtracted image generated by subtracting model lens galaxy image from phase 1.
    # 2) Fix our mass model to the lens galaxy mass-model from phase 2.
    # 3) Use a circular annular mask which includes only the source-galaxy light.

    class InversionPhase(ph.LensSourcePlanePhase):

        def modify_image(self, image, previous_results):
            return image - previous_results[2].unmasked_lens_plane_model_image

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.mass = previous_results[1].constant.lens.mass
            self.lens_galaxies.lens.shear = previous_results[1].constant.lens.shear

    phase4 = InversionPhase(lens_galaxies=dict(lens=gm.GalaxyModel(mass=mp.EllipticalIsothermal,
                                                                   shear=mp.ExternalShear)),
                            source_galaxies=dict(source=gm.GalaxyModel(pixelization=pix.AdaptiveMagnification,
                                                                      regularization=reg.Constant)),
                            optimizer_class=nl.MultiNest, mask_function=mask_function_annular,
                            phase_name=pipeline_path + '/phase_4_inversion_init')

    phase4.optimizer.const_efficiency_mode = True
    phase4.optimizer.n_live_points = 20
    phase4.optimizer.sampling_efficiency = 0.8

    ### PHASE 5 ###

    # In phase 5, we fit the len galaxy light, mass and source galxy simultaneously, using an inversion. We will:

    # 1) Initialize the priors of the lens galaxy and source galaxy from phases 3+4.
    # 2) Use a circular mask which includes the lens and source galaxy light.

    class InversionPhase(ph.LensSourcePlanePhase):

        def pass_priors(self, previous_results):

            self.lens_galaxies.lens.light = previous_results[2].variable.lens.light
            self.lens_galaxies.lens.mass = previous_results[2].variable.lens.mass
            self.lens_galaxies.lens.shear = previous_results[2].variable.lens.shear
            self.source_galaxies.source = previous_results[3].variable.source

    phase5 = InversionPhase(lens_galaxies=dict(lens=gm.GalaxyModel(light=lp.EllipticalSersic,
                                                                   mass=mp.EllipticalIsothermal,
                                                                   shear=mp.ExternalShear)),
                            source_galaxies=dict(source=gm.GalaxyModel(pixelization=pix.AdaptiveMagnification,
                                                                      regularization=reg.Constant)),
                            optimizer_class=nl.MultiNest, mask_function=mask_function_circular,
                            phase_name=pipeline_path + '/phase_5_inversion')

    phase5.optimizer.const_efficiency_mode = True
    phase5.optimizer.n_live_points = 60
    phase5.optimizer.sampling_efficiency = 0.4

    return pipeline.PipelineImaging(pipeline_path, phase1, phase2, phase3, phase4, phase5)
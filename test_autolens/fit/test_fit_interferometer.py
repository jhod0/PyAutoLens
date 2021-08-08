import autolens as al
import numpy as np
import pytest
from autoarray.inversion.inversion.interferometer import InversionInterferometerMatrix
from autoarray.inversion.inversion.interferometer import (
    InversionInterferometerLinearOperator,
)
from autogalaxy.mock.mock import MockLightProfile


class TestFitProperties:
    def test__total_inversions(self, interferometer_7):
        g0 = al.Galaxy(redshift=0.5)

        g1 = al.Galaxy(redshift=1.0)

        g2 = al.Galaxy(redshift=2.0)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        assert fit.total_inversions == 0

        g2 = al.Galaxy(
            redshift=2.0,
            pixelization=al.pix.Rectangular(),
            regularization=al.reg.Constant(),
        )

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        assert fit.total_inversions == 1

        g0 = al.Galaxy(
            redshift=0.5,
            pixelization=al.pix.Rectangular(),
            regularization=al.reg.Constant(),
        )

        g1 = al.Galaxy(
            redshift=1.0,
            pixelization=al.pix.Rectangular(),
            regularization=al.reg.Constant(),
        )

        g2 = al.Galaxy(
            redshift=2.0,
            pixelization=al.pix.Rectangular(),
            regularization=al.reg.Constant(),
        )

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        assert fit.total_inversions == 3


class TestLikelihood:
    def test__1x2_image__1x2_visibilities__simple_fourier_transform(self):
        # The image plane image generated by the galaxy is [1.0, 1.0]

        # Thus the chi squared is 4.0**2.0 + 3.0**2.0 = 25.0

        uv_wavelengths = np.array([[0.0, 0.0]])

        real_space_mask = al.Mask2D.manual(
            mask=np.array(
                [
                    [True, True, True, True],
                    [True, False, False, True],
                    [True, True, True, True],
                ]
            ),
            pixel_scales=1.0,
        )

        interferometer = al.Interferometer(
            visibilities=al.Visibilities.full(fill_value=5.0, shape_slim=(1,)),
            noise_map=al.Visibilities.ones(shape_slim=(1,)),
            uv_wavelengths=uv_wavelengths,
            real_space_mask=real_space_mask,
            settings=al.SettingsInterferometer(
                sub_size=1, transformer_class=al.TransformerDFT
            ),
        )

        interferometer.visibilities[0] = 5.0 + 4.0j

        # Setup as a ray trace instance, using a light profile for the lens

        g0 = al.Galaxy(redshift=0.5, light_profile=MockLightProfile(value=1.0, size=2))
        tracer = al.Tracer.from_galaxies(galaxies=[g0])

        fit = al.FitInterferometer(interferometer=interferometer, tracer=tracer)

        assert (fit.visibilities.slim == np.array([5.0 + 4.0j])).all()
        assert (fit.noise_map.slim == np.array([1.0 + 1.0j])).all()
        assert (fit.model_visibilities.slim == np.array([2.0 + 0.0j])).all()
        assert (fit.residual_map.slim == np.array([3.0 + 4.0j])).all()
        assert (fit.normalized_residual_map.slim == np.array([3.0 + 4.0j])).all()
        assert (fit.chi_squared_map.slim == np.array([9.0 + 16.0j])).all()

        assert fit.chi_squared == 25.0
        assert fit.noise_normalization == (2.0 * np.log(2 * np.pi * 1.0 ** 2.0))
        assert fit.log_likelihood == -0.5 * (
            25.0 + 2.0 * np.log(2 * np.pi * 1.0 ** 2.0)
        )

    def test__3x2_image__2x2_visibilities__use_transformer_for_likelihood(self):

        uv_wavelengths = np.array([[1.0, 0.0], [1.0, 1.0], [2.0, 2.0]])

        real_space_mask = al.Mask2D.unmasked(shape_native=(1, 3), pixel_scales=1.0)

        transformer = al.TransformerDFT(
            uv_wavelengths=uv_wavelengths, real_space_mask=real_space_mask
        )

        real_space_mask = al.Mask2D.manual(
            mask=np.array(
                [
                    [True, True, True, True, True],
                    [True, False, False, False, True],
                    [True, True, True, True, True],
                ]
            ),
            pixel_scales=1.0,
        )

        interferometer = al.Interferometer(
            visibilities=al.Visibilities.full(fill_value=5.0, shape_slim=(3,)),
            noise_map=al.Visibilities.full(fill_value=2.0, shape_slim=(3,)),
            uv_wavelengths=uv_wavelengths,
            real_space_mask=real_space_mask,
            settings=al.SettingsInterferometer(
                sub_size=1, transformer_class=al.TransformerDFT
            ),
        )

        # Setup as a ray trace instance, using a light profile for the lens

        g0 = al.Galaxy(redshift=0.5, light_profile=al.lp.EllSersic(intensity=0.001))

        image = g0.image_2d_from_grid(grid=interferometer.grid)

        model_visibilities_manual = transformer.visibilities_from_image(image=image)

        tracer = al.Tracer.from_galaxies(galaxies=[g0])

        fit = al.FitInterferometer(interferometer=interferometer, tracer=tracer)

        assert (
            fit.visibilities.slim == np.array([5.0 + 5.0j, 5.0 + 5.0j, 5.0 + 5.0j])
        ).all()
        assert (
            fit.noise_map.slim == np.array([2.0 + 2.0j, 2.0 + 2.0j, 2.0 + 2.0j])
        ).all()

        assert fit.model_visibilities.slim == pytest.approx(
            model_visibilities_manual, 1.0e-4
        )

        # moddel visibilities are all [1.94805, 0.0]

        assert fit.residual_map.slim == pytest.approx(
            np.array([3.0519 + 5.0j, 3.0519 + 5.0j, 3.0519 + 5.0j]), 1.0e-4
        )

        assert fit.normalized_residual_map.slim == pytest.approx(
            np.array(
                [
                    3.0519 / 2.0 + (5.0 / 2.0) * 1.0j,
                    3.0519 / 2.0 + (5.0 / 2.0) * 1.0j,
                    3.0519 / 2.0 + (5.0 / 2.0) * 1.0j,
                ]
            ),
            1.0e-4,
        )

        assert fit.chi_squared_map.slim == pytest.approx(
            np.array(
                [
                    (3.0519 / 2.0) ** 2.0 + ((5.0 / 2.0) ** 2.0) * 1.0j,
                    (3.0519 / 2.0) ** 2.0 + ((5.0 / 2.0) ** 2.0) * 1.0j,
                    (3.0519 / 2.0) ** 2.0 + ((5.0 / 2.0) ** 2.0) * 1.0j,
                ]
            ),
            1.0e-4,
        )

        assert fit.chi_squared == pytest.approx(25.73579, 1.0e-4)
        assert fit.noise_normalization == pytest.approx(
            (6.0 * np.log(2 * np.pi * 2.0 ** 2.0)), 1.0e-4
        )
        assert fit.log_likelihood == pytest.approx(
            -0.5 * (25.73579 + 6.0 * np.log(2 * np.pi * 2.0 ** 2.0)), 1.0e-4
        )

    def test__hyper_background_changes_background_sky__reflected_in_likelihood(self,):

        uv_wavelengths = np.array([[1.0, 0.0], [1.0, 1.0], [2.0, 2.0]])

        real_space_mask = al.Mask2D.manual(
            mask=np.array(
                [
                    [True, True, True, True, True],
                    [True, False, False, False, True],
                    [True, True, True, True, True],
                ]
            ),
            pixel_scales=1.0,
        )

        interferometer = al.Interferometer(
            visibilities=al.Visibilities.full(fill_value=5.0, shape_slim=(3,)),
            noise_map=al.Visibilities.full(fill_value=2.0, shape_slim=(3,)),
            uv_wavelengths=uv_wavelengths,
            real_space_mask=real_space_mask,
            settings=al.SettingsInterferometer(sub_size=1),
        )

        # Setup as a ray trace instance, using a light profile for the lens

        g0 = al.Galaxy(redshift=0.5, light_profile=MockLightProfile(value=1.0, size=2))
        tracer = al.Tracer.from_galaxies(galaxies=[g0])

        hyper_background_noise = al.hyper_data.HyperBackgroundNoise(noise_scale=1.0)

        fit = al.FitInterferometer(
            interferometer=interferometer,
            tracer=tracer,
            hyper_background_noise=hyper_background_noise,
        )

        assert (
            fit.visibilities.slim == (1.0 + 1.0j) * np.full(fill_value=5.0, shape=(3,))
        ).all()

        assert (
            fit.noise_map.slim == (1.0 + 1.0j) * np.full(fill_value=3.0, shape=(3,))
        ).all()


class TestCompareToManualProfilesOnly:
    def test___all_lens_fit_quantities__no_hyper_methods(self, interferometer_7):
        g0 = al.Galaxy(
            redshift=0.5,
            light_profile=al.lp.EllSersic(intensity=1.0),
            mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
        )

        g1 = al.Galaxy(redshift=1.0, light_profile=al.lp.EllSersic(intensity=1.0))

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        assert interferometer_7.noise_map == pytest.approx(fit.noise_map)

        model_visibilities = tracer.profile_visibilities_from_grid_and_transformer(
            grid=interferometer_7.grid, transformer=interferometer_7.transformer
        )

        assert model_visibilities == pytest.approx(fit.model_visibilities, 1e-4)

        residual_map = al.util.fit.residual_map_from(
            data=interferometer_7.visibilities, model_data=model_visibilities
        )

        assert residual_map == pytest.approx(fit.residual_map, 1e-4)

        normalized_residual_map = al.util.fit.normalized_residual_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7.noise_map
        )

        assert normalized_residual_map == pytest.approx(
            fit.normalized_residual_map, 1e-4
        )

        chi_squared_map = al.util.fit.chi_squared_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7.noise_map
        )

        assert chi_squared_map == pytest.approx(fit.chi_squared_map, 1e-4)

        chi_squared = al.util.fit.chi_squared_complex_from(
            chi_squared_map=fit.chi_squared_map
        )

        noise_normalization = al.util.fit.noise_normalization_complex_from(
            noise_map=interferometer_7.noise_map
        )

        log_likelihood = al.util.fit.log_likelihood_from(
            chi_squared=chi_squared, noise_normalization=noise_normalization
        )

        assert log_likelihood == pytest.approx(fit.log_likelihood, 1e-4)
        assert log_likelihood == fit.figure_of_merit

    def test___lens_fit_galaxy_model_image_dict__corresponds_to_profile_galaxy_images(
        self, interferometer_7_grid
    ):
        g0 = al.Galaxy(
            redshift=0.5,
            light_profile=al.lp.EllSersic(intensity=1.0),
            mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
        )
        g1 = al.Galaxy(redshift=1.0, light_profile=al.lp.EllSersic(intensity=1.0))
        g2 = al.Galaxy(redshift=1.0)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

        fit = al.FitInterferometer(interferometer=interferometer_7_grid, tracer=tracer)

        traced_grids_of_planes = tracer.traced_grids_of_planes_from_grid(
            grid=interferometer_7_grid.grid
        )

        g0_image = g0.image_2d_from_grid(grid=traced_grids_of_planes[0])

        g1_image = g1.image_2d_from_grid(grid=traced_grids_of_planes[1])

        assert fit.galaxy_model_image_dict[g0].slim == pytest.approx(g0_image, 1.0e-4)
        assert fit.galaxy_model_image_dict[g1].slim == pytest.approx(g1_image, 1.0e-4)

    def test___lens_fit_galaxy_visibilities_dict__corresponds_to_galaxy_visibilities(
        self, interferometer_7_grid
    ):
        g0 = al.Galaxy(
            redshift=0.5,
            light_profile=al.lp.EllSersic(intensity=1.0),
            mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
        )
        g1 = al.Galaxy(redshift=1.0, light_profile=al.lp.EllSersic(intensity=1.0))
        g2 = al.Galaxy(redshift=1.0)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2])

        fit = al.FitInterferometer(interferometer=interferometer_7_grid, tracer=tracer)

        traced_grids_of_planes = tracer.traced_grids_of_planes_from_grid(
            grid=interferometer_7_grid.grid
        )

        g0_profile_visibilities = g0.profile_visibilities_from_grid_and_transformer(
            grid=traced_grids_of_planes[0],
            transformer=interferometer_7_grid.transformer,
        )

        g1_profile_visibilities = g1.profile_visibilities_from_grid_and_transformer(
            grid=traced_grids_of_planes[1],
            transformer=interferometer_7_grid.transformer,
        )

        assert fit.galaxy_model_visibilities_dict[g0].slim == pytest.approx(
            g0_profile_visibilities, 1.0e-4
        )
        assert fit.galaxy_model_visibilities_dict[g1].slim == pytest.approx(
            g1_profile_visibilities, 1.0e-4
        )
        assert (
            fit.galaxy_model_visibilities_dict[g2].slim == (0.0 + 0.0j) * np.zeros((7,))
        ).all()

        assert fit.model_visibilities.slim == pytest.approx(
            fit.galaxy_model_visibilities_dict[g0].slim
            + fit.galaxy_model_visibilities_dict[g1].slim,
            1.0e-4,
        )

    def test___all_lens_fit_quantities__hyper_background_noise(self, interferometer_7):

        hyper_background_noise = al.hyper_data.HyperBackgroundNoise(noise_scale=1.0)

        hyper_noise_map = hyper_background_noise.hyper_noise_map_from_complex_noise_map(
            noise_map=interferometer_7.noise_map
        )

        g0 = al.Galaxy(
            redshift=0.5,
            light_profile=al.lp.EllSersic(intensity=1.0),
            mass_profile=al.mp.SphIsothermal(einstein_radius=1.0),
        )

        g1 = al.Galaxy(redshift=1.0, light_profile=al.lp.EllSersic(intensity=1.0))

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

        fit = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            hyper_background_noise=hyper_background_noise,
        )

        assert hyper_noise_map.slim == pytest.approx(fit.noise_map.slim)

        fit = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            hyper_background_noise=hyper_background_noise,
            use_hyper_scaling=False,
        )

        assert fit.noise_map == pytest.approx(interferometer_7.noise_map, 1.0e-4)
        assert fit.noise_map != pytest.approx(hyper_noise_map.slim, 1.0e-4)


class TestCompareToManualInversionOnly:
    def test___all_lens_fit_quantities__no_hyper_methods(self, interferometer_7):

        # Ensures the inversion grid is used, as this would cause the test to fail.
        interferometer_7.grid[0, 0] = -100.0

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=0.01)

        g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7.grid_inversion, sparse_grid=None
        )

        inversion = InversionInterferometerMatrix.from_data_mapper_and_regularization(
            mapper=mapper,
            regularization=reg,
            visibilities=interferometer_7.visibilities,
            noise_map=interferometer_7.noise_map,
            transformer=interferometer_7.transformer,
        )

        assert inversion.mapped_reconstructed_visibilities == pytest.approx(
            fit.model_visibilities, 1.0e-4
        )

        residual_map = al.util.fit.residual_map_from(
            data=interferometer_7.visibilities,
            model_data=inversion.mapped_reconstructed_visibilities,
        )

        assert residual_map.slim == pytest.approx(fit.residual_map.slim, 1.0e-4)

        normalized_residual_map = al.util.fit.normalized_residual_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7.noise_map
        )

        assert normalized_residual_map.slim == pytest.approx(
            fit.normalized_residual_map.slim, 1.0e-4
        )

        chi_squared_map = al.util.fit.chi_squared_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7.noise_map
        )

        assert chi_squared_map.slim == pytest.approx(fit.chi_squared_map.slim, 1.0e-4)

        chi_squared = al.util.fit.chi_squared_complex_from(
            chi_squared_map=fit.chi_squared_map
        )

        noise_normalization = al.util.fit.noise_normalization_complex_from(
            noise_map=interferometer_7.noise_map
        )

        log_likelihood = al.util.fit.log_likelihood_from(
            chi_squared=chi_squared, noise_normalization=noise_normalization
        )

        assert log_likelihood == pytest.approx(fit.log_likelihood, 1e-4)

        log_likelihood_with_regularization = al.util.fit.log_likelihood_with_regularization_from(
            chi_squared=chi_squared,
            regularization_term=inversion.regularization_term,
            noise_normalization=noise_normalization,
        )

        assert log_likelihood_with_regularization == pytest.approx(
            fit.log_likelihood_with_regularization, 1e-4
        )

        log_evidence = al.util.fit.log_evidence_from(
            chi_squared=chi_squared,
            regularization_term=inversion.regularization_term,
            log_curvature_regularization_term=inversion.log_det_curvature_reg_matrix_term,
            log_regularization_term=inversion.log_det_regularization_matrix_term,
            noise_normalization=noise_normalization,
        )

        assert log_evidence == fit.log_evidence
        assert log_evidence == fit.figure_of_merit

        mapped_reconstructed_image = al.util.inversion.mapped_reconstructed_data_via_mapping_matrix_from(
            mapping_matrix=fit.inversion.mapper.mapping_matrix,
            reconstruction=fit.inversion.reconstruction,
        )

        assert (
            fit.inversion.mapped_reconstructed_image.slim == mapped_reconstructed_image
        ).all()

    def test___lens_fit_galaxy_model_image_dict__images_and_inversion_mapped_reconstructed_image(
        self, interferometer_7
    ):
        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=1.0)

        g0 = al.Galaxy(redshift=0.5)
        g1 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7.grid, sparse_grid=None
        )

        inversion = InversionInterferometerMatrix.from_data_mapper_and_regularization(
            mapper=mapper,
            regularization=reg,
            visibilities=interferometer_7.visibilities,
            noise_map=interferometer_7.noise_map,
            transformer=interferometer_7.transformer,
        )

        assert (fit.galaxy_model_image_dict[g0].native == np.zeros((7, 7))).all()

        assert fit.galaxy_model_image_dict[g1].slim == pytest.approx(
            inversion.mapped_reconstructed_image.slim, 1.0e-4
        )

    def test___lens_fit_galaxy_model_visibilities_dict__has_inversion_mapped_reconstructed_visibilities(
        self, interferometer_7
    ):
        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=1.0)

        g0 = al.Galaxy(redshift=0.5)
        g1 = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7.grid, sparse_grid=None
        )

        inversion = InversionInterferometerMatrix.from_data_mapper_and_regularization(
            mapper=mapper,
            regularization=reg,
            visibilities=interferometer_7.visibilities,
            noise_map=interferometer_7.noise_map,
            transformer=interferometer_7.transformer,
        )

        assert (
            fit.galaxy_model_visibilities_dict[g0] == (0.0 + 0.0j) * np.zeros((7,))
        ).all()

        assert fit.galaxy_model_visibilities_dict[g1].slim == pytest.approx(
            inversion.mapped_reconstructed_visibilities.slim, 1.0e-4
        )

        assert fit.model_visibilities.slim == pytest.approx(
            fit.galaxy_model_visibilities_dict[g1].slim, 1.0e-4
        )

    def test___all_lens_fit_quantities__hyper_background_noise(self, interferometer_7):

        hyper_background_noise = al.hyper_data.HyperBackgroundNoise(noise_scale=1.0)

        hyper_noise_map = hyper_background_noise.hyper_noise_map_from_complex_noise_map(
            noise_map=interferometer_7.noise_map
        )

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=0.01)

        g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

        fit = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            hyper_background_noise=hyper_background_noise,
        )

        assert hyper_noise_map.slim == pytest.approx(fit.inversion.noise_map, 1.0e-4)

        assert hyper_noise_map.slim == pytest.approx(fit.noise_map.slim)

    def test___stochastic_mode_gives_different_log_likelihood_list(
        self, interferometer_7
    ):

        pix = al.pix.VoronoiBrightnessImage(pixels=9)
        reg = al.reg.Constant(coefficient=1.0)

        g0 = al.Galaxy(
            redshift=0.5,
            pixelization=pix,
            regularization=reg,
            hyper_model_image=al.Array2D.ones(shape_native=(3, 3), pixel_scales=1.0),
            hyper_galaxy_image=al.Array2D.ones(shape_native=(3, 3), pixel_scales=1.0),
        )

        tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

        fit_0 = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            settings_pixelization=al.SettingsPixelization(is_stochastic=False),
        )
        fit_1 = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            settings_pixelization=al.SettingsPixelization(is_stochastic=False),
        )

        assert fit_0.log_evidence == fit_1.log_evidence

        fit_0 = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            settings_pixelization=al.SettingsPixelization(is_stochastic=True),
        )
        fit_1 = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            settings_pixelization=al.SettingsPixelization(is_stochastic=True),
        )

        assert fit_0.log_evidence != fit_1.log_evidence

    def test___all_lens_fit_quantities__linear_operator(self, interferometer_7_lop):

        # Ensures the inversion grid is used, as this would cause the test to fail.
        interferometer_7_lop.grid[0, 0] = -100.0

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=0.01)

        g0 = al.Galaxy(redshift=0.5, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[al.Galaxy(redshift=0.5), g0])

        fit = al.FitInterferometer(
            interferometer=interferometer_7_lop,
            tracer=tracer,
            settings_inversion=al.SettingsInversion(use_linear_operators=True),
        )

        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7_lop.grid_inversion, sparse_grid=None
        )

        inversion = InversionInterferometerLinearOperator.from_data_mapper_and_regularization(
            mapper=mapper,
            regularization=reg,
            visibilities=interferometer_7_lop.visibilities,
            noise_map=interferometer_7_lop.noise_map,
            transformer=interferometer_7_lop.transformer,
            settings=al.SettingsInversion(use_linear_operators=True),
        )

        assert inversion.mapped_reconstructed_visibilities == pytest.approx(
            fit.model_visibilities, 1.0e-4
        )

        residual_map = al.util.fit.residual_map_from(
            data=interferometer_7_lop.visibilities,
            model_data=inversion.mapped_reconstructed_visibilities,
        )

        assert residual_map.slim == pytest.approx(fit.residual_map.slim, 1.0e-4)

        normalized_residual_map = al.util.fit.normalized_residual_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7_lop.noise_map
        )

        assert normalized_residual_map.slim == pytest.approx(
            fit.normalized_residual_map.slim, 1.0e-4
        )

        chi_squared_map = al.util.fit.chi_squared_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7_lop.noise_map
        )

        assert chi_squared_map.slim == pytest.approx(fit.chi_squared_map.slim, 1.0e-4)

        chi_squared = al.util.fit.chi_squared_complex_from(
            chi_squared_map=chi_squared_map
        )

        noise_normalization = al.util.fit.noise_normalization_complex_from(
            noise_map=interferometer_7_lop.noise_map
        )

        log_likelihood = al.util.fit.log_likelihood_from(
            chi_squared=chi_squared, noise_normalization=noise_normalization
        )

        assert log_likelihood == pytest.approx(fit.log_likelihood, 1e-4)

        log_likelihood_with_regularization = al.util.fit.log_likelihood_with_regularization_from(
            chi_squared=chi_squared,
            regularization_term=inversion.regularization_term,
            noise_normalization=noise_normalization,
        )

        assert log_likelihood_with_regularization == pytest.approx(
            fit.log_likelihood_with_regularization, 1e-4
        )

        log_evidence = al.util.fit.log_evidence_from(
            chi_squared=chi_squared,
            regularization_term=inversion.regularization_term,
            log_curvature_regularization_term=inversion.log_det_curvature_reg_matrix_term,
            log_regularization_term=inversion.log_det_regularization_matrix_term,
            noise_normalization=noise_normalization,
        )

        assert log_evidence == fit.log_evidence
        assert log_evidence == fit.figure_of_merit

        mapped_reconstructed_image = al.util.inversion.mapped_reconstructed_data_via_mapping_matrix_from(
            mapping_matrix=fit.inversion.mapper.mapping_matrix,
            reconstruction=fit.inversion.reconstruction,
        )

        assert (
            fit.inversion.mapped_reconstructed_image.slim == mapped_reconstructed_image
        ).all()


class TestCompareToManualProfilesAndInversion:
    def test___all_lens_fit_quantities__no_hyper_methods(self, interferometer_7):
        galaxy_light = al.Galaxy(
            redshift=0.5, light_profile=al.lp.EllSersic(intensity=1.0)
        )

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=1.0)
        galaxy_pix = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[galaxy_light, galaxy_pix])

        fit = al.FitInterferometer(interferometer=interferometer_7, tracer=tracer)

        profile_visibilities = tracer.profile_visibilities_from_grid_and_transformer(
            grid=interferometer_7.grid, transformer=interferometer_7.transformer
        )

        assert profile_visibilities.slim == pytest.approx(fit.profile_visibilities.slim)

        profile_subtracted_visibilities = (
            interferometer_7.visibilities - profile_visibilities
        )

        assert profile_subtracted_visibilities.slim == pytest.approx(
            fit.profile_subtracted_visibilities.slim
        )

        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7.grid,
            settings=al.SettingsPixelization(use_border=False),
        )

        inversion = InversionInterferometerMatrix.from_data_mapper_and_regularization(
            visibilities=profile_subtracted_visibilities,
            noise_map=interferometer_7.noise_map,
            transformer=interferometer_7.transformer,
            mapper=mapper,
            regularization=reg,
        )

        model_visibilities = (
            profile_visibilities + inversion.mapped_reconstructed_visibilities
        )

        assert model_visibilities.slim == pytest.approx(fit.model_visibilities.slim)

        residual_map = al.util.fit.residual_map_from(
            data=interferometer_7.visibilities, model_data=model_visibilities
        )

        assert residual_map.slim == pytest.approx(fit.residual_map.slim)

        normalized_residual_map = al.util.fit.normalized_residual_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7.noise_map
        )

        assert normalized_residual_map.slim == pytest.approx(
            fit.normalized_residual_map.slim
        )

        chi_squared_map = al.util.fit.chi_squared_map_complex_from(
            residual_map=residual_map, noise_map=interferometer_7.noise_map
        )

        assert chi_squared_map.slim == pytest.approx(fit.chi_squared_map.slim)

        chi_squared = al.util.fit.chi_squared_complex_from(
            chi_squared_map=chi_squared_map
        )

        noise_normalization = al.util.fit.noise_normalization_complex_from(
            noise_map=interferometer_7.noise_map
        )

        log_likelihood = al.util.fit.log_likelihood_from(
            chi_squared=chi_squared, noise_normalization=noise_normalization
        )

        assert log_likelihood == pytest.approx(fit.log_likelihood, 1e-4)

        log_likelihood_with_regularization = al.util.fit.log_likelihood_with_regularization_from(
            chi_squared=chi_squared,
            regularization_term=inversion.regularization_term,
            noise_normalization=noise_normalization,
        )

        assert log_likelihood_with_regularization == pytest.approx(
            fit.log_likelihood_with_regularization, 1e-4
        )

        log_evidence = al.util.fit.log_evidence_from(
            chi_squared=chi_squared,
            regularization_term=inversion.regularization_term,
            log_curvature_regularization_term=inversion.log_det_curvature_reg_matrix_term,
            log_regularization_term=inversion.log_det_regularization_matrix_term,
            noise_normalization=noise_normalization,
        )

        assert log_evidence == fit.log_evidence
        assert log_evidence == fit.figure_of_merit

        mapped_reconstructed_image = al.util.inversion.mapped_reconstructed_data_via_mapping_matrix_from(
            mapping_matrix=fit.inversion.mapper.mapping_matrix,
            reconstruction=fit.inversion.reconstruction,
        )

        assert (
            fit.inversion.mapped_reconstructed_image.slim == mapped_reconstructed_image
        ).all()

    def test___lens_fit_galaxy_model_visibilities_dict__has_image_and_inversion_mapped_reconstructed_image(
        self, interferometer_7_grid
    ):

        g0 = al.Galaxy(redshift=0.5, light_profile=al.lp.EllSersic(intensity=1.0))
        g1 = al.Galaxy(redshift=0.5, light_profile=al.lp.EllSersic(intensity=2.0))
        g2 = al.Galaxy(redshift=0.5)

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=1.0)
        galaxy_pix = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2, galaxy_pix])

        fit = al.FitInterferometer(interferometer=interferometer_7_grid, tracer=tracer)

        traced_grids = tracer.traced_grids_of_planes_from_grid(
            grid=interferometer_7_grid.grid
        )

        g0_visibilities = g0.profile_visibilities_from_grid_and_transformer(
            grid=traced_grids[0], transformer=interferometer_7_grid.transformer
        )

        g1_visibilities = g1.profile_visibilities_from_grid_and_transformer(
            grid=traced_grids[1], transformer=interferometer_7_grid.transformer
        )

        profile_visibilities = g0_visibilities + g1_visibilities

        profile_subtracted_visibilities = (
            interferometer_7_grid.visibilities - profile_visibilities
        )
        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7_grid.grid,
            settings=al.SettingsPixelization(use_border=False),
        )

        inversion = InversionInterferometerMatrix.from_data_mapper_and_regularization(
            visibilities=profile_subtracted_visibilities,
            noise_map=interferometer_7_grid.noise_map,
            transformer=interferometer_7_grid.transformer,
            mapper=mapper,
            regularization=reg,
        )

        g0_image = g0.image_2d_from_grid(grid=traced_grids[0])

        g1_image = g1.image_2d_from_grid(grid=traced_grids[1])

        assert (fit.galaxy_model_image_dict[g2].native == np.zeros((7, 7))).all()

        assert fit.galaxy_model_image_dict[g0].slim == pytest.approx(
            g0_image.slim, 1.0e-4
        )
        assert fit.galaxy_model_image_dict[g1].slim == pytest.approx(
            g1_image.slim, 1.0e-4
        )
        assert fit.galaxy_model_image_dict[galaxy_pix].slim == pytest.approx(
            inversion.mapped_reconstructed_image.slim, 1.0e-4
        )

    def test___lens_fit_galaxy_model_visibilities_dict__has_profile_visibilitiess_and_inversion_mapped_reconstructed_visibilities(
        self, interferometer_7_grid
    ):

        g0 = al.Galaxy(redshift=0.5, light_profile=al.lp.EllSersic(intensity=1.0))
        g1 = al.Galaxy(redshift=0.5, light_profile=al.lp.EllSersic(intensity=2.0))
        g2 = al.Galaxy(redshift=0.5)

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=1.0)
        galaxy_pix = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[g0, g1, g2, galaxy_pix])

        fit = al.FitInterferometer(interferometer=interferometer_7_grid, tracer=tracer)

        traced_grids = tracer.traced_grids_of_planes_from_grid(
            grid=interferometer_7_grid.grid
        )

        g0_visibilities = g0.profile_visibilities_from_grid_and_transformer(
            grid=traced_grids[0], transformer=interferometer_7_grid.transformer
        )

        g1_visibilities = g1.profile_visibilities_from_grid_and_transformer(
            grid=traced_grids[1], transformer=interferometer_7_grid.transformer
        )

        profile_visibilities = g0_visibilities + g1_visibilities

        profile_subtracted_visibilities = (
            interferometer_7_grid.visibilities - profile_visibilities
        )
        mapper = pix.mapper_from_grid_and_sparse_grid(
            grid=interferometer_7_grid.grid,
            settings=al.SettingsPixelization(use_border=False),
        )

        inversion = InversionInterferometerMatrix.from_data_mapper_and_regularization(
            visibilities=profile_subtracted_visibilities,
            noise_map=interferometer_7_grid.noise_map,
            transformer=interferometer_7_grid.transformer,
            mapper=mapper,
            regularization=reg,
        )

        assert (
            fit.galaxy_model_visibilities_dict[g2] == (0.0 + 0.0j) * np.zeros((7,))
        ).all()

        assert fit.galaxy_model_visibilities_dict[g0].slim == pytest.approx(
            g0_visibilities.slim, 1.0e-4
        )
        assert fit.galaxy_model_visibilities_dict[g1].slim == pytest.approx(
            g1_visibilities.slim, 1.0e-4
        )
        assert fit.galaxy_model_visibilities_dict[galaxy_pix].slim == pytest.approx(
            inversion.mapped_reconstructed_visibilities.slim, 1.0e-4
        )

        assert fit.model_visibilities.slim == pytest.approx(
            fit.galaxy_model_visibilities_dict[g0].slim
            + fit.galaxy_model_visibilities_dict[g1].slim
            + inversion.mapped_reconstructed_visibilities.slim,
            1.0e-4,
        )

    def test___all_lens_fit_quantities__hyper_background_noise(self, interferometer_7):

        hyper_background_noise = al.hyper_data.HyperBackgroundNoise(noise_scale=1.0)

        hyper_noise_map = hyper_background_noise.hyper_noise_map_from_complex_noise_map(
            noise_map=interferometer_7.noise_map
        )

        galaxy_light = al.Galaxy(
            redshift=0.5, light_profile=al.lp.EllSersic(intensity=1.0)
        )

        pix = al.pix.Rectangular(shape=(3, 3))
        reg = al.reg.Constant(coefficient=1.0)
        galaxy_pix = al.Galaxy(redshift=1.0, pixelization=pix, regularization=reg)

        tracer = al.Tracer.from_galaxies(galaxies=[galaxy_light, galaxy_pix])

        fit = al.FitInterferometer(
            interferometer=interferometer_7,
            tracer=tracer,
            hyper_background_noise=hyper_background_noise,
        )

        assert hyper_noise_map.slim == pytest.approx(fit.inversion.noise_map, 1.0e-4)

        assert hyper_noise_map.slim == pytest.approx(fit.noise_map.slim)

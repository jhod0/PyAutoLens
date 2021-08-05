from autoarray.plot.mat_wrap import mat_plot as mp
from autolens.analysis.subhalo import SubhaloSearchResult
from autoarray.plot import abstract_plotters
from autogalaxy.plot.mat_wrap import lensing_mat_plot, lensing_include, lensing_visuals
from autolens.fit.fit_imaging import FitImaging
from autolens.plot import fit_imaging_plotters

import numpy as np


class SubhaloPlotter(abstract_plotters.AbstractPlotter):
    def __init__(
        self,
        subhalo_result: SubhaloSearchResult,
        fit_imaging_detect,
        use_log_evidences: bool = True,
        use_stochastic_log_evidences: bool = False,
        mat_plot_2d: lensing_mat_plot.MatPlot2D = lensing_mat_plot.MatPlot2D(),
        visuals_2d: lensing_visuals.Visuals2D = lensing_visuals.Visuals2D(),
        include_2d: lensing_include.Include2D = lensing_include.Include2D(),
    ):
        super().__init__(
            mat_plot_2d=mat_plot_2d, include_2d=include_2d, visuals_2d=visuals_2d
        )

        self.subhalo_result = subhalo_result
        self.fit_imaging_detect = fit_imaging_detect
        self.use_log_evidences = use_log_evidences
        self.use_stochastic_log_evidences = use_stochastic_log_evidences

    @property
    def fit_imaging_before(self):
        return self.subhalo_result.result_no_subhalo.max_log_likelihood_fit

    @property
    def fit_imaging_before_plotter(self):
        return fit_imaging_plotters.FitImagingPlotter(
            fit=self.fit_imaging_before,
            mat_plot_2d=self.mat_plot_2d,
            visuals_2d=self.visuals_2d,
            include_2d=self.include_2d,
        )

    @property
    def fit_imaging_detect_plotter(self):
        return self.fit_imaging_detect_plotter_from(visuals_2d=self.visuals_2d)

    def fit_imaging_detect_plotter_from(self, visuals_2d):
        return fit_imaging_plotters.FitImagingPlotter(
            fit=self.fit_imaging_detect,
            mat_plot_2d=self.mat_plot_2d,
            visuals_2d=visuals_2d,
            include_2d=self.include_2d,
        )

    def detection_array_from(self, remove_zeros: bool = False):

        detection_array = self.subhalo_result.subhalo_detection_array_from(
            use_log_evidences=self.use_log_evidences,
            use_stochastic_log_evidences=self.use_stochastic_log_evidences,
        )

        if remove_zeros:

            detection_array[detection_array < 0.0] = 0.0

        return detection_array

    def figure_with_detection_overlay(
        self, image: bool = False, remove_zeros: bool = False, show_median: bool = True
    ):

        median_detection = np.round(np.median(self.detection_array_from()), 2)

        visuals_2d = self.visuals_2d + self.visuals_2d.__class__(
            array_overlay=self.detection_array_from(remove_zeros=remove_zeros),
            mass_profile_centres=self.subhalo_result.centres_native,
        )

        fit_imaging_plotter = self.fit_imaging_detect_plotter_from(
            visuals_2d=visuals_2d
        )

        if show_median:
            fit_imaging_plotter.set_title(label=f"Image {median_detection}")
            fit_imaging_plotter.figures_2d(image=image)

    def subplot_detection_imaging(self, remove_zeros: bool = False):

        self.open_subplot_figure(number_subplots=4)

        self.set_title("Image")
        self.fit_imaging_detect_plotter.figures_2d(image=True)

        self.set_title("Signal-To-Noise Map")
        self.fit_imaging_detect_plotter.figures_2d(signal_to_noise_map=True)
        self.set_title(None)

        self.mat_plot_2d.plot_array(
            array=self.detection_array_from(remove_zeros=remove_zeros),
            visuals_2d=self.visuals_2d,
            auto_labels=mp.AutoLabels(title="Increase in Log Evidence"),
        )

        mass_array = self.subhalo_result.subhalo_mass_array_from()

        self.mat_plot_2d.plot_array(
            array=mass_array,
            visuals_2d=self.visuals_2d,
            auto_labels=mp.AutoLabels(title="Subhalo Mass"),
        )

        self.mat_plot_2d.output.subplot_to_figure(
            auto_filename="subplot_detection_imaging"
        )
        self.close_subplot_figure()

    def subplot_detection_fits(self):
        """
        A subplot comparing the normalized residuals, chi-squared map and source reconstructions of the model-fits
        before the subhalo added to the model (top row) and the subhalo fit which gives the largest increase in
        Bayesian evidence on the subhalo detection grid search.

        Parameters
        ----------
        fit_imaging_before : FitImaging
            The fit of a `Tracer` not including a subhalo in the model to a `MaskedImaging` dataset (e.g. the
            model-image, residual_map, chi_squared_map).
        fit_imaging_detect : FitImaging
            The fit of a `Tracer` with the subhalo detection grid's highest evidence model including a subhalo to a
            `MaskedImaging` dataset (e.g. the  model-image, residual_map, chi_squared_map).
        include : Include
            Customizes what appears on the plots (e.g. critical curves, profile centres, origin, etc.).
        mat_plot_2d : Plotter
            Object for plotting PyAutoLens data-stuctures as subplots via Matplotlib.
        """

        self.open_subplot_figure(number_subplots=6)

        self.set_title("Normalized Residuals (No Subhalo)")
        self.fit_imaging_before_plotter.figures_2d(normalized_residual_map=True)

        self.set_title("Chi-Squared Map (No Subhalo)")
        self.fit_imaging_before_plotter.figures_2d(chi_squared_map=True)

        self.set_title("Source Reconstruction (No Subhalo)")
        self.fit_imaging_before_plotter.figures_2d_of_planes(
            plane_image=True, plane_index=1
        )

        self.set_title("Normailzed Residuals (With Subhalo)")
        self.fit_imaging_detect_plotter.figures_2d(normalized_residual_map=True)

        self.set_title("Chi-Squared Map (With Subhalo)")
        self.fit_imaging_detect_plotter.figures_2d(chi_squared_map=True)

        self.set_title("Source Reconstruction (With Subhalo)")
        self.fit_imaging_detect_plotter.figures_2d_of_planes(
            plane_image=True, plane_index=1
        )

        self.mat_plot_2d.output.subplot_to_figure(
            auto_filename="subplot_detection_fits"
        )
        self.close_subplot_figure()

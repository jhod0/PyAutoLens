from autoarray.plot.mat_wrap import mat_plot as mp
from autoarray.plot import abstract_plotters
from autogalaxy.plot.mat_wrap import lensing_mat_plot, lensing_include, lensing_visuals
from autolens.dataset import point_source


class PointDatasetPlotter(abstract_plotters.AbstractPlotter):
    def __init__(
        self,
        point_dataset: point_source.PointDataset,
        mat_plot_1d: lensing_mat_plot.MatPlot1D = lensing_mat_plot.MatPlot1D(),
        visuals_1d: lensing_visuals.Visuals1D = lensing_visuals.Visuals1D(),
        include_1d: lensing_include.Include1D = lensing_include.Include1D(),
        mat_plot_2d: lensing_mat_plot.MatPlot2D = lensing_mat_plot.MatPlot2D(),
        visuals_2d: lensing_visuals.Visuals2D = lensing_visuals.Visuals2D(),
        include_2d: lensing_include.Include2D = lensing_include.Include2D(),
    ):
        super().__init__(
            mat_plot_1d=mat_plot_1d,
            visuals_1d=visuals_1d,
            include_1d=include_1d,
            mat_plot_2d=mat_plot_2d,
            include_2d=include_2d,
            visuals_2d=visuals_2d,
        )

        self.point_dataset = point_dataset

    @property
    def visuals_with_include_2d(self) -> lensing_visuals.Visuals2D:
        """
        Extracts from a `Structure` attributes that can be plotted and return them in a `Visuals` object.

        Only attributes with `True` entries in the `Include` object are extracted for plotting.

        From an `AbstractStructure` the following attributes can be extracted for plotting:

        - origin: the (y,x) origin of the structure's coordinate system.
        - mask: the mask of the structure.
        - border: the border of the structure's mask.

        Parameters
        ----------
        structure : abstract_structure.AbstractStructure
            The structure whose attributes are extracted for plotting.

        Returns
        -------
        vis.Visuals2D
            The collection of attributes that can be plotted by a `Plotter2D` object.
        """

        return self.visuals_2d

    def figures_2d(self, positions: bool = False, fluxes: bool = False):

        if positions:

            self.mat_plot_2d.plot_grid(
                grid=self.point_dataset.positions,
                y_errors=self.point_dataset.positions_noise_map,
                x_errors=self.point_dataset.positions_noise_map,
                visuals_2d=self.visuals_with_include_2d,
                auto_labels=mp.AutoLabels(
                    title=f"{self.point_dataset.name} (Positions)",
                    filename="point_dataset_positions",
                ),
                buffer=0.1,
            )

        if fluxes:

            if self.point_dataset.fluxes is not None:

                self.mat_plot_2d.plot_grid(
                    grid=self.point_dataset.positions,
                    y_errors=self.point_dataset.positions_noise_map,
                    x_errors=self.point_dataset.positions_noise_map,
                    color_array=self.point_dataset.fluxes,
                    visuals_2d=self.visuals_with_include_2d,
                    auto_labels=mp.AutoLabels(
                        title=f" {self.point_dataset.name} (Fluxes)",
                        filename="point_dataset_fluxes",
                    ),
                    buffer=0.1,
                )

    def subplot(
        self,
        positions: bool = False,
        fluxes: bool = False,
        auto_filename="subplot_point_dataset",
    ):

        self._subplot_custom_plot(
            positions=positions,
            fluxes=fluxes,
            auto_labels=mp.AutoLabels(filename=auto_filename),
        )

    def subplot_point_dataset(self):
        self.subplot(positions=True, fluxes=True)
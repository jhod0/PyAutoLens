import numpy as np

import autofit as af
import autolens as al


class GalaxiesMockAnalysis:
    def __init__(self, number_galaxies, value):
        self.number_galaxies = number_galaxies
        self.value = value
        self.hyper_model_image = None
        self.hyper_galaxy_image_path_dict = None

    # noinspection PyUnusedLocal
    def galaxy_images_for_model(self, model):
        return self.number_galaxies * [np.array([self.value])]

    def fit(self, instance):
        return 1


class MockResult:
    def __init__(
        self,
        instance=None,
        likelihood=None,
        model=None,
        mask=None,
        model_image=None,
        hyper_galaxy_image_path_dict=None,
        hyper_model_image=None,
        galaxy_images=(),
        model_visibilities=None,
        galaxy_visibilities=(),
        analysis=None,
        optimizer=None,
        pixelization=None,
        positions=None,
        updated_positions=None,
        updated_positions_threshold=None,
        use_as_hyper_dataset=False,
    ):
        self.instance = instance
        self.likelihood = likelihood
        self.model = model
        self.previous_model = model
        self.gaussian_tuples = None
        self.mask_2d = None
        self.positions = None
        self.mask_2d = mask
        self.hyper_galaxy_image_path_dict = hyper_galaxy_image_path_dict
        self.hyper_model_image = hyper_model_image
        self.model_image = model_image
        self.unmasked_model_image = model_image
        self.galaxy_images = galaxy_images
        self.model_visibilities = model_visibilities
        self.galaxy_visibilities = galaxy_visibilities
        self.instance = instance or af.ModelInstance()
        self.model = af.ModelMapper()
        self.analysis = analysis
        self.optimizer = optimizer
        self.pixelization = pixelization
        self.hyper_combined = MockHyperCombinedPhase()
        self.use_as_hyper_dataset = use_as_hyper_dataset
        self.positions = positions
        self.updated_positions = (
            updated_positions if updated_positions is not None else []
        )
        self.updated_positions_threshold = updated_positions_threshold
        self.most_likely_tracer = al.Tracer.from_galaxies(
            galaxies=[al.Galaxy(redshift=0.5)]
        )

    @property
    def visibilities_galaxy_dict(self) -> {str: al.Galaxy}:
        """
        A dictionary associating galaxy names with model visibilities of those galaxies
        """
        return {
            galaxy_path: self.galaxy_visibilities[i]
            for i, galaxy_path, galaxy in self.path_galaxy_tuples_with_index
        }

    @property
    def hyper_galaxy_visibilities_path_dict(self):
        """
        A dictionary associating 1D hyper_galaxies galaxy visibilities with their names.
        """

        hyper_galaxy_visibilities_path_dict = {}

        for path, galaxy in self.path_galaxy_tuples:

            hyper_galaxy_visibilities_path_dict[path] = self.visibilities_galaxy_dict[
                path
            ]

        return hyper_galaxy_visibilities_path_dict

    @property
    def hyper_model_visibilities(self):

        hyper_model_visibilities = al.Visibilities.zeros(
            shape_1d=(self.galaxy_visibilities[0].shape_1d,)
        )

        for path, galaxy in self.path_galaxy_tuples:
            hyper_model_visibilities += self.hyper_galaxy_visibilities_path_dict[path]

        return hyper_model_visibilities

    @property
    def last(self):
        return self

    @property
    def image_plane_multiple_image_positions_of_source_plane_centres(self):
        return self.updated_positions


class MockResults(af.ResultsCollection):
    def __init__(
        self,
        instance=None,
        likelihood=None,
        analysis=None,
        optimizer=None,
        model=None,
        mask=None,
        model_image=None,
        hyper_galaxy_image_path_dict=None,
        hyper_model_image=None,
        galaxy_images=(),
        model_visibilities=None,
        galaxy_visibilities=(),
        pixelization=None,
        positions=None,
        updated_positions=None,
        updated_positions_threshold=None,
        use_as_hyper_dataset=False,
    ):
        """
        A collection of results from previous phases. Results can be obtained using an index or the name of the phase
        from whence they came.
        """

        result = MockResult(
            instance=instance,
            likelihood=likelihood,
            analysis=analysis,
            optimizer=optimizer,
            model=model,
            mask=mask,
            model_image=model_image,
            galaxy_images=galaxy_images,
            hyper_galaxy_image_path_dict=hyper_galaxy_image_path_dict,
            hyper_model_image=hyper_model_image,
            model_visibilities=model_visibilities,
            galaxy_visibilities=galaxy_visibilities,
            pixelization=pixelization,
            positions=positions,
            updated_positions=updated_positions,
            updated_positions_threshold=updated_positions_threshold,
            use_as_hyper_dataset=use_as_hyper_dataset,
        )

        self.__result_list = [result]
        self.__result_dict = {}

    def copy(self):
        collection = MockResults()
        collection.__result_dict = self.__result_dict
        collection.__result_list = self.__result_list
        return collection

    @property
    def reversed(self):
        return reversed(self.__result_list)

    @property
    def last(self):
        """
        The result of the last phase
        """
        if len(self.__result_list) > 0:
            return self.__result_list[-1]
        return None

    @property
    def first(self):
        """
        The result of the first phase
        """
        if len(self.__result_list) > 0:
            return self.__result_list[0]
        return None

    def add(self, phase_name, result):
        """
        Add the result of a phase.

        Parameters
        ----------
        phase_name: str
            The name of the phase
        result
            The result of that phase
        """
        try:
            self.__result_list[self.__result_list.index(result)] = result
        except ValueError:
            self.__result_list.append(result)
        self.__result_dict[phase_name] = result

    def __getitem__(self, item):
        """
        Get the result of a previous phase by index

        Parameters
        ----------
        item: int
            The index of the result

        Returns
        -------
        result: Result
            The result of a previous phase
        """
        return self.__result_list[item]

    def __len__(self):
        return len(self.__result_list)

    def __contains__(self, item):
        return item in self.__result_dict


class MockHyperCombinedPhase:
    def __init__(self):
        pass

    @property
    def most_likely_pixelization_grids_of_planes(self):
        return 1


class MockNLO(af.NonLinearOptimizer):
    def _simple_fit(self, analysis, fitness_function):
        # noinspection PyTypeChecker
        return af.Result(None, analysis.fit(None), None)

    def _fit(self, analysis, model):
        class Fitness:
            def __init__(self, instance_from_vector):
                self.result = None
                self.instance_from_vector = instance_from_vector

            def __call__(self, vector):
                instance = self.instance_from_vector(vector)

                likelihood = analysis.fit(instance)
                self.result = MockResult(instance, likelihood)

                # Return Chi squared
                return -2 * likelihood

        fitness_function = Fitness(model.instance_from_vector)
        fitness_function(model.prior_count * [0.8])

        return fitness_function.result

    def output_from_model(self, model, paths):
        return MockOutput()


class MockOutput:
    def __init__(self):
        pass

    @property
    def most_likely_instance(self):
        self.galaxies = [
            al.Galaxy(redshift=0.5, light=al.lp.EllipticalSersic(centre=(0.0, 1.0))),
            al.Galaxy(redshift=1.0, light=al.lp.EllipticalSersic()),
        ]

        return self

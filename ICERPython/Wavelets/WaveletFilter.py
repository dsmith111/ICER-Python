import json
import numpy as np

class WaveletFilter:
    filter_parameters = {
        "a-1": 0,
        "a0": 0,
        "a1": 0,
        "B": 0
    }
    filter_name = None

    def __init__(self, filter_selection, filter_parameters_path):
        with open(filter_parameters_path, "r") as f:
            self.all_filter_parameters = json.load(f)

        self.filter_parameters = self.all_filter_parameters["filters"][filter_selection]
        self.filter_name = filter_selection

    # Convert the filter parameters to a numpy array
    def get_filter_parameters(self):
        return np.array([el for el in self.filter_parameters.values()])
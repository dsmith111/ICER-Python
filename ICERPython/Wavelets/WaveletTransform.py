import numpy as np
from ICERPython.Wavelets.Filters.HighPassFilters import HighPassFilter
from ICERPython.Wavelets.Filters.LowPassFilters import LowPassFilter

class WaveletTransform:
    def __init__(self, input_image, filter_parameters):
        self.decompLevels = {
            1: {"LL": None, "HL": None, "LH": None, "HH": None},
        }
        self.input_image = input_image
        self.image_queue = [input_image]
        self.filter_parameters = filter_parameters.get_filter_parameters()

    def low_pass_filter(self, data):
        low_pass = LowPassFilter(data)
        return low_pass.compute_outputs()

    def high_pass_filter(self, data, low_pass_outputs):
        high_pass = HighPassFilter(data, low_pass_outputs, self.filter_parameters)
        high_pass.compute_dn()
        high_pass.compute_rn()
        return high_pass.compute_outputs()

    def _apply_transform_on_rows(self, data):
        height, width = data.shape
        expected_width = (width // 2) - 1
        low_pass_rows = np.zeros((height, expected_width))
        high_pass_rows = np.zeros((height, expected_width))

        for row in range(height):
            low_pass_outputs = self.low_pass_filter(data[row, :])
            high_pass_outputs = self.high_pass_filter(data[row, :], low_pass_outputs)
            
            low_pass_rows[row, :] = low_pass_outputs[:expected_width]
            high_pass_rows[row, :] = high_pass_outputs[:expected_width]

        return low_pass_rows, high_pass_rows

    def _apply_transform_on_columns(self, data):
        height, width = data.shape
        expected_height = (height // 2) - 1
        low_pass_columns = np.zeros((expected_height, width))
        high_pass_columns = np.zeros((expected_height, width))

        for col in range(width):
            low_pass_outputs = self.low_pass_filter(data[:, col])
            high_pass_outputs = self.high_pass_filter(data[:, col], low_pass_outputs)
            
            low_pass_columns[:, col] = low_pass_outputs[:expected_height]
            high_pass_columns[:, col] = high_pass_outputs[:expected_height]

        return low_pass_columns, high_pass_columns


    # Two-dimensional wavelet transform
    def forward_transform(self, levels=1):
        
        # Iterative decomposition preferred over recursive decomposition
        for level in range(levels):
            temp_image_queue = []
            # Implement forward wavelet transform on rows (this will return <L>*, and <H>*)
            for image in self.image_queue:
                low_pass_rows, high_pass_rows = self._apply_transform_on_rows(image)

                # Implement forward wavelet transform on columns (this will return <L>L, <L>H then <H>L, <H>H)
                (LL, LH) = self._apply_transform_on_columns(low_pass_rows)
                (HL, HH) = self._apply_transform_on_columns(high_pass_rows)
                
                # Update image queue if there are more levels to compute
                low_freq_band = LL
                if level < levels - 1:
                    temp_image_queue.append(low_freq_band)
                    low_freq_band = None
                    
                    
                # Update decomp levels dictionary
                self.decompLevels[level+1] = {"LL": low_freq_band, "HL": HL, "LH": LH, "HH": HH}
            
            self.image_queue = temp_image_queue
        
        self.image_queue = [self.input_image]
                    
        return self.decompLevels


    def inverse_transform(self, low_pass_columns, high_pass_columns):
        # Implement inverse wavelet transform
        # Note: This implementation depends on the specific wavelet transform and reconstruction method used in the paper.
        pass

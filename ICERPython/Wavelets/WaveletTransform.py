import numpy as np
from ICERPython.Wavelets.Filters.HighPassFilters import HighPassFilter
from ICERPython.Wavelets.Filters.LowPassFilters import LowPassFilter

class WaveletTransform:
    def __init__(self, input_image, filter_parameters):
        self.decompLevels = {
            1: {"LL": None, "HL": None, "LH": None, "HH": None},
        }
        self.input_image = np.asarray(input_image, dtype=np.int64)
        if self.input_image.ndim != 2 or self.input_image.size == 0:
            raise ValueError("Input image must be a nonempty grayscale array")
        self.image_queue = [self.input_image]
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
        low_pass_rows = np.zeros((height, (width + 1) // 2), dtype=np.int64)
        high_pass_rows = np.zeros((height, width // 2), dtype=np.int64)

        for row in range(height):
            low_pass_outputs = self.low_pass_filter(data[row, :])
            high_pass_outputs = self.high_pass_filter(data[row, :], low_pass_outputs)
            
            low_pass_rows[row, :] = low_pass_outputs
            high_pass_rows[row, :] = high_pass_outputs

        return low_pass_rows, high_pass_rows

    def _apply_transform_on_columns(self, data):
        height, width = data.shape
        low_pass_columns = np.zeros(((height + 1) // 2, width), dtype=np.int64)
        high_pass_columns = np.zeros((height // 2, width), dtype=np.int64)

        for col in range(width):
            low_pass_outputs = self.low_pass_filter(data[:, col])
            high_pass_outputs = self.high_pass_filter(data[:, col], low_pass_outputs)
            
            low_pass_columns[:, col] = low_pass_outputs
            high_pass_columns[:, col] = high_pass_outputs

        return low_pass_columns, high_pass_columns


    # Two-dimensional wavelet transform
    def forward_transform(self, levels=1):
        max_levels = max(1, (max(self.input_image.shape) - 1).bit_length())
        if not isinstance(levels, int) or levels < 1 or levels > max_levels:
            raise ValueError("Invalid number of wavelet decomposition levels")
        self.decompLevels = {}
        self.image_queue = [self.input_image]

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


    def _inverse_filter(self, low_pass_outputs, high_pass_outputs):
        length = len(low_pass_outputs) + len(high_pass_outputs)
        high_pass = HighPassFilter(np.zeros(length), low_pass_outputs, self.filter_parameters)
        high_pass.compute_rn()
        for i in range(len(high_pass_outputs) - 1, -1, -1):
            high_pass.d_n_outputs[i] = high_pass_outputs[i] + high_pass._compute_prediction(i)

        outputs = np.zeros(length, dtype=np.int64)
        for i in range(len(high_pass_outputs)):
            outputs[2 * i] = low_pass_outputs[i] + (high_pass.d_n_outputs[i] + 1) // 2
            outputs[2 * i + 1] = outputs[2 * i] - high_pass.d_n_outputs[i]
        if length % 2 != 0:
            outputs[-1] = low_pass_outputs[-1]
        return outputs

    def _apply_inverse_on_columns(self, low_pass_columns, high_pass_columns):
        height = low_pass_columns.shape[0] + high_pass_columns.shape[0]
        width = low_pass_columns.shape[1]
        outputs = np.zeros((height, width), dtype=np.int64)
        for col in range(width):
            outputs[:, col] = self._inverse_filter(low_pass_columns[:, col], high_pass_columns[:, col])
        return outputs

    def inverse_transform(self, low_pass_columns=None, high_pass_columns=None):
        if high_pass_columns is not None:
            return self._apply_inverse_on_columns(low_pass_columns, high_pass_columns)

        subbands = self.decompLevels if low_pass_columns is None else low_pass_columns
        low_freq_band = subbands[max(subbands)]["LL"]
        for level in sorted(subbands, reverse=True):
            low_pass_rows = self._apply_inverse_on_columns(low_freq_band, subbands[level]["LH"])
            high_pass_rows = self._apply_inverse_on_columns(subbands[level]["HL"], subbands[level]["HH"])
            height = low_pass_rows.shape[0]
            width = low_pass_rows.shape[1] + high_pass_rows.shape[1]
            low_freq_band = np.zeros((height, width), dtype=np.int64)
            for row in range(height):
                low_freq_band[row, :] = self._inverse_filter(low_pass_rows[row, :], high_pass_rows[row, :])
        return low_freq_band

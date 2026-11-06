import numpy as np
import math

class HighPassFilter:
    low_pass_outputs = None
    d_n_outputs = None
    r_n_outputs = None
    filter_parameters = None

    def __init__(self, data: np.array, low_pass_outputs: np.array, filter_parameters: np.array):
        self.data = data
        self.N = len(data)
        self.low_pass_outputs = low_pass_outputs
        self.d_n_outputs = np.zeros((self.N + 1) // 2, dtype=np.int64)
        self.r_n_outputs = np.zeros((self.N + 1) // 2, dtype=np.int64)
        self.filter_parameters = filter_parameters

    # Implement d(n) computation
    def compute_dn(self):
        for i in range(self.N // 2):
            self.d_n_outputs[i] = self._dn_even_data_computation(i)

    # Implement r(n) computation
    def compute_rn(self):
        for i in range(len(self.low_pass_outputs)):
            if i == 0:
                continue

            self.r_n_outputs[i] = self.low_pass_outputs[i-1] - self.low_pass_outputs[i]

    # Implement high-pass filter output computation
    def compute_outputs(self):
        outputs = np.zeros(self.N // 2, dtype=np.int64)
        for i in range(self.N // 2):
            outputs[i] = self.d_n_outputs[i] - self._compute_prediction(i)
        
        return outputs

    def _compute_prediction(self, i):
        if i == 0:
            value = self._hn_zero_data_computation(i)
        elif i == self.N // 2 - 1 and self.N % 2 == 0:
            value = self._hn_end_even_data_computation(i)
        elif i == 1 and self.filter_parameters[0] != 0:
            value = self._hn_one_data_computation(i)
        else:
            value = self._hn_standard_data_computation(i)
        return math.floor(value)


    def _dn_even_data_computation(self, i):
        return int(self.data[2 * i]) - int(self.data[2 * i + 1])
    
    # Conditonal for i == 0
    def _hn_zero_data_computation(self, i):
        if len(self.r_n_outputs) < 2:
            return 0
        return (1/4) * self.r_n_outputs[1]
    
    # Conditional for i == 1 and filter_parameters[0] != 0
    def _hn_one_data_computation(self, i):
        a = (1/4) * self.r_n_outputs[1]
        b = (3/8) * self.r_n_outputs[2]
        c = (1/4) * self.d_n_outputs[2]
        return a + b - c + 0.5
    
    # Conditional for N is even and i == N/2 - 1
    def _hn_end_even_data_computation(self, i):
        return (1/4) * self.r_n_outputs[math.floor((self.N/2) - 1)]
    
    # Conditonal for everything else
    def _hn_standard_data_computation(self, i):
        a = self.filter_parameters[0] * self.r_n_outputs[i-1]
        b = self.filter_parameters[1] * self.r_n_outputs[i]
        c = self.filter_parameters[2] * self.r_n_outputs[i+1]
        d = self.filter_parameters[3] * self.d_n_outputs[i+1]
        return a + b + c - d + 0.5
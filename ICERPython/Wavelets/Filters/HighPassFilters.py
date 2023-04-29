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
        self.d_n_outputs = np.zeros(self.N)
        self.r_n_outputs = np.zeros(self.N)
        self.filter_parameters = filter_parameters

    # Implement d(n) computation
    def compute_dn(self):
        stopping_point = math.floor((self.N / 2) - 1)
        is_odd = False

        if self.N % 2 == 0:
            is_odd = True

        outputs = np.zeros(self.N)

        # If the length of the data is even, we only need to compute the first (N / 2) - 1 outputs
        for i in range(self.N):
            if i < stopping_point:
                # Compute the output value for even data length
                outputs[i] = self._dn_even_data_computation(i)
            elif i >= stopping_point and is_odd == False:
                # Compute the output value for even data length and break the loop
                outputs[i] = self._dn_even_data_computation(i)
                break
            else:
                # If the length of the data is odd, we need to zero out the last output rounded up
                outputs[i] = 0
                break

        self.d_n_outputs = outputs

    # Implement r(n) computation
    def compute_rn(self):
        for i in range(len(self.low_pass_outputs)):
            if i == 0:
                continue

            self.r_n_outputs[i] = self.low_pass_outputs[i-1] - self.low_pass_outputs[i]

    # Implement high-pass filter output computation
    def compute_outputs(self):
        stopping_point = math.floor((self.N / 2) - 1)
        is_odd = False

        if self.N % 2 == 0:
            is_odd = True

        outputs = np.zeros(stopping_point)
        for i in range(stopping_point):
            
            if i == 0:
                outputs[i] = self.d_n_outputs[i] - self._hn_zero_data_computation(i)
            elif i == 1 and self.filter_parameters[0] != 0:
                outputs[i] = self.d_n_outputs[i] - self._hn_one_data_computation(i)
            elif i == stopping_point - 1 and is_odd == False:
                outputs[i] = self.d_n_outputs[i] - self._hn_end_even_data_computation(i)
            else:
                outputs[i] = self.d_n_outputs[i] - self._hn_standard_data_computation(i)
        
        return outputs



    def _dn_even_data_computation(self, i):
        return self.data[2 * i] - self.data[2 * i + 1]
    
    # Conditonal for i == 0
    def _hn_zero_data_computation(self, i):
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
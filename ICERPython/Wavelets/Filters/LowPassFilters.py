import numpy as np
import math

class LowPassFilter:
    def __init__(self, data: np.array):
        self.data = data
        self.N = len(data)

    def compute_outputs(self):
        # Implement low-pass filter operation
        stopping_point = math.ceil((self.N / 2) - 1)
        is_odd = False

        if self.N % 2 == 0:
            is_odd = True

        outputs = np.zeros(self.N)

        # If the length of the data is even, we only need to compute the first (N / 2) - 1 outputs
        for i in range(self.N):
            if i < stopping_point:
                # Compute the output value for even data length
                outputs[i] = self._even_data_computation(i)
            elif i >= stopping_point and is_odd == False:
                # Compute the output value for even data length and break the loop
                outputs[i] = self._even_data_computation(i)
                break
            else:
                # If the length of the data is odd, we need to zero out the last output rounded up
                outputs[i] = self.data[i-1]
                break

        return outputs
    
    def _even_data_computation(self, i):
        return 0.5 * (self.data[2 * i] + self.data[(2 * i) + 1])

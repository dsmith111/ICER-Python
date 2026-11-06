import numpy as np
import math

class LowPassFilter:
    def __init__(self, data: np.array):
        self.data = data
        self.N = len(data)

    def compute_outputs(self):
        # Implement low-pass filter operation
        outputs = np.zeros((self.N + 1) // 2, dtype=np.int64)
        for i in range(self.N // 2):
            outputs[i] = self._even_data_computation(i)

        if self.N % 2 != 0:
            outputs[-1] = self.data[-1]

        return outputs
    
    def _even_data_computation(self, i):
        return (int(self.data[2 * i]) + int(self.data[(2 * i) + 1])) // 2

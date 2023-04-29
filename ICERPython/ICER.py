import numpy as np
from ICERPython.BitPlaneCoding import helpers as bitplane_helpers
from ICERPython.BitPlaneCoding import Models as bitplane_models
from ICERPython.BitPlaneCoding.BitPlaneEncoder import BitPlaneEncoder

# Progressive image compression using wavelet transform
class ICER:
    def __init__(self, wavelet_transform):
        self.wavelet_transform = wavelet_transform

    def lossless_compression(self, levels: int = 1):
        # Implement lossless compression
        # 1. Perform forward wavelet transform
        print("Performing forward wavelet transform...")
        subbands = self.wavelet_transform.forward_transform(levels)

        # 2. Create numpy array of bitplane models
        print("Constructing bitplanes...")
        bitplanes = bitplane_helpers.construct_bit_planes(subbands)
        
        # 3. Encode the bitplanes (e.g., using entropy coding)
        print("Encoding bitplanes...")
        bitplane_encoder = BitPlaneEncoder(bitplanes)
        bitplane_encoder.encode_bit_planes()
        
        # Note: This step depends on the specific encoding method used in the paper.
        print("Done encoding bitplanes.")
        return subbands

    def lossy_compression(self, bitrate, levels: int = 1):
        # Implement lossy compression with specified bitrate
        # 1. Perform forward wavelet transform
        subbands = self.wavelet_transform.forward_transform(levels)

        # 2. Quantize the transform coefficients using a specified bitrate
        # Note: This step depends on the specific quantization method used in the paper.
        pass

        # 3. Encode the quantized coefficients (e.g., using entropy coding)
        # Note: This step depends on the specific encoding method used in the paper.
        pass

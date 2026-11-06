import ICERPython.BitPlaneCoding.Models as Models
import numpy as np
from ICERPython.BitPlaneCoding import helpers
from ICERPython.BitPlaneCoding.Models.ContextModel import ContextModel
from ICERPython.BitPlaneCoding.ProbabilityEstimation import ProbabilityEstimation
from ICERPython.EntropyCoding.EntropyCoder import EntropyCoder
from tqdm import tqdm

class BitPlaneEncoder:
    
    def __init__(self, bitPlanes: list, subbands=None):
        self.bitPlanes = bitPlanes
        self.bitPlanePriorities = np.empty(len(bitPlanes), dtype=object)
        self.subbands = subbands
        self.metadata = {}
    
    def _set_bitPlanePriorities(self, bitPlanes: list[Models.BitPlaneModel]):
        for i, bitPlane in enumerate(bitPlanes):
            self.bitPlanePriorities[i] = bitPlane
            
    def _sort_bit_planes(self):
        # Custom sorting key function
        # Sort the bit planes using the custom key function
        self.bitPlanes = sorted(self.bitPlanes, key=helpers.bit_plane_sort_key)

    def _get_subband_information(self):
        information = {}
        for bit_plane in self.bitPlanes:
            key = (bit_plane.levelOfDecomp, bit_plane.subband)
            height, width = bit_plane.bitPlaneMatrix.shape
            if key not in information:
                information[key] = [key[0], key[1], height, width, 0]
            information[key][4] = max(information[key][4], bit_plane.bitNum + 1)
        if self.subbands is not None:
            for level, subbands in self.subbands.items():
                for subband, matrix in subbands.items():
                    if matrix is not None and (level, subband) not in information:
                        information[(level, subband)] = [level, subband, *matrix.shape, 0]
        return list(information.values())
        
    def encode_bit_planes(self, byte_quota=None, minimum_loss=0, show_progress=True):
        if not isinstance(minimum_loss, int) or minimum_loss < 0:
            raise ValueError("Minimum loss must be a nonnegative integer")
        if byte_quota is not None and (not isinstance(byte_quota, int) or byte_quota < 0):
            raise ValueError("Byte quota must be a nonnegative integer")
        # Implement the bit-plane encoding process
        # Encode the bit planes starting from MSB down to LSB
        self._sort_bit_planes()
        bit_planes = [bit_plane for bit_plane in self.bitPlanes if bit_plane.priority >= minimum_loss]
        entropy_coder = EntropyCoder()
        states = {}
        plane_count = 0

        # Loop through each bitplane (where each bitplane is a numpy 2D array of pixels) in bitplanes
        for i in tqdm(range(len(bit_planes)), disable=not show_progress):
            if byte_quota is not None and entropy_coder.bit_count >= byte_quota * 8:
                break
            bit_plane = bit_planes[i]
            key = (bit_plane.levelOfDecomp, bit_plane.subband)
            if key not in states:
                bit_plane.categoryMatrix.fill(0)
                states[key] = {"context": ContextModel(), "signs": np.zeros(bit_plane.bitPlaneMatrix.shape, dtype=int),
                               "neighbors": {position: np.zeros(bit_plane.bitPlaneMatrix.shape, dtype=int)
                                             for position in ["horizontal", "vertical", "diagonal"]}}
            state = states[key]
            bit_plane.context = state["context"]
            probability = ProbabilityEstimation(bit_plane.context)
            # Loop through each pixel in raster scan order (row by row)
            for row in range(bit_plane.bitPlaneMatrix.shape[0]):
                for col in range(bit_plane.bitPlaneMatrix.shape[1]):
                    # Get the current bit
                    current_bit = bit_plane.bitPlaneMatrix[row, col]
                    
                    # Get the current category
                    current_category = bit_plane.get_categories([(row, col)])[0]

                    neighbors = {position: counts[row, col] for position, counts in state["neighbors"].items()}
                    
                    # Get current context
                    current_context = helpers.determine_context(current_category, bit_plane.subband, neighbors)

                    # Update and set context
                    entropy_coder.encode(current_bit, probability.estimate_probability(current_context))
                    probability.update_counts(current_context, current_bit)
                    
                    # Update category
                    if current_category == 0 and current_bit == 1:
                        coordinates = helpers.get_neighbors((row, col), bit_plane.bitPlaneMatrix)
                        sign_context, prediction = helpers.determine_sign_context(bit_plane.subband, coordinates, state["signs"])
                        sign_bit = int(bit_plane.signMatrix[row, col] < 0)
                        agreement_bit = sign_bit ^ prediction
                        entropy_coder.encode(agreement_bit, probability.estimate_probability(sign_context))
                        probability.update_counts(sign_context, agreement_bit)
                        state["signs"][row, col] = -1 if sign_bit else 1
                        helpers.update_neighbor_counts(coordinates, state["neighbors"])
                        bit_plane.update_category((row, col), 1)
                    elif current_category > 0:
                        bit_plane.update_category((row, col), min([current_category + 1, 3]))
            plane_count += 1

        encoded_bit_stream = entropy_coder.finish()
        self.metadata = {"subbands": self._get_subband_information(), "planeCount": plane_count,
                         "bitCount": entropy_coder.bit_count, "minimumLoss": minimum_loss,
                         "bufferSize": entropy_coder.buffer_size}
        return encoded_bit_stream


            


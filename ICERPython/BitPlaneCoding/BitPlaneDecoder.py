import numpy as np
from ICERPython.BitPlaneCoding import helpers
from ICERPython.BitPlaneCoding.Models.BitPlaneModel import BitPlaneModel
from ICERPython.BitPlaneCoding.Models.ContextModel import ContextModel
from ICERPython.BitPlaneCoding.ProbabilityEstimation import ProbabilityEstimation
from ICERPython.EntropyCoding.EntropyCoder import EntropyDecoder

class BitPlaneDecoder:
    def __init__(self, metadata=None):
        self.metadata = metadata
        self.complete = False

    def decode_bit_planes(self, encoded_bit_stream, metadata=None, allow_partial=False):
        metadata = self.metadata if metadata is None else metadata
        if metadata is None:
            raise ValueError("Bit-plane metadata is required for decoding")
        self.metadata = metadata
        states = {}
        bit_planes = []
        subbands = {}
        for level, subband, height, width, bit_count in metadata["subbands"]:
            shape = (height, width)
            if level < 1 or subband not in ["LL", "HL", "LH", "HH"] or min(shape) < 0 or not 0 <= bit_count <= 62:
                raise ValueError("Invalid subband metadata")
            if (level, subband) in states:
                raise ValueError("Duplicate subband metadata")
            state = {"context": ContextModel(), "categories": np.zeros(shape, dtype=int),
                     "signs": np.zeros(shape, dtype=int), "magnitude": np.zeros(shape, dtype=np.int64),
                     "remaining": np.full(shape, bit_count, dtype=int),
                     "neighbors": {position: np.zeros(shape, dtype=int)
                                   for position in ["horizontal", "vertical", "diagonal"]}}
            states[(level, subband)] = state
            subbands.setdefault(level, {"LL": None, "HL": None, "LH": None, "HH": None})
            for bit_num in range(bit_count):
                bit_plane = BitPlaneModel(level, bit_num, subband, state["magnitude"], state["context"],
                                          state["categories"], state["signs"])
                if bit_plane.priority >= metadata["minimumLoss"]:
                    bit_planes.append(bit_plane)
        bit_planes = sorted(bit_planes, key=helpers.bit_plane_sort_key)
        if not 0 <= metadata["planeCount"] <= len(bit_planes):
            raise ValueError("Invalid encoded plane count")
        bit_count = metadata["bitCount"]
        if allow_partial:
            bit_count = min(bit_count, len(encoded_bit_stream) * 8)
        entropy_decoder = EntropyDecoder(encoded_bit_stream, bit_count, metadata["bufferSize"])
        self.complete = True
        try:
            for bit_plane in bit_planes[:metadata["planeCount"]]:
                state = states[(bit_plane.levelOfDecomp, bit_plane.subband)]
                probability = ProbabilityEstimation(state["context"])
                for row in range(bit_plane.bitPlaneMatrix.shape[0]):
                    for col in range(bit_plane.bitPlaneMatrix.shape[1]):
                        current_category = state["categories"][row, col]
                        neighbors = {position: counts[row, col] for position, counts in state["neighbors"].items()}
                        current_context = helpers.determine_context(current_category, bit_plane.subband, neighbors)
                        current_bit = entropy_decoder.decode(probability.estimate_probability(current_context))
                        probability.update_counts(current_context, current_bit)
                        if current_category == 0 and current_bit == 1:
                            coordinates = helpers.get_neighbors((row, col), bit_plane.bitPlaneMatrix)
                            sign_context, prediction = helpers.determine_sign_context(bit_plane.subband, coordinates, state["signs"])
                            agreement_bit = entropy_decoder.decode(probability.estimate_probability(sign_context))
                            probability.update_counts(sign_context, agreement_bit)
                            state["signs"][row, col] = -1 if agreement_bit ^ prediction else 1
                            helpers.update_neighbor_counts(coordinates, state["neighbors"])
                            state["categories"][row, col] = 1
                        elif current_category > 0:
                            state["categories"][row, col] = min([current_category + 1, 3])
                        state["magnitude"][row, col] |= current_bit << bit_plane.bitNum
                        state["remaining"][row, col] = bit_plane.bitNum
        except EOFError:
            self.complete = False
            if not allow_partial:
                raise

        for (level, subband), state in states.items():
            midpoint = (1 << np.maximum(state["remaining"] - 1, 0)) - 1
            magnitude = np.where(state["magnitude"] > 0, state["magnitude"] + midpoint, 0)
            subbands[level][subband] = magnitude * state["signs"]
        return subbands

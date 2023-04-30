import ICERPython.BitPlaneCoding.Models as Models
import numpy as np
from ICERPython.BitPlaneCoding import helpers
from tqdm import tqdm

class BitPlaneEncoder:
    
    def __init__(self, bitPlanes: list):
        self.bitPlanes = bitPlanes
        self.bitPlanePriorities = np.zeros(len(bitPlanes), dtype=int)
    
    def _set_bitPlanePriorities(self, bitPlanes: list[Models.BitPlaneModel]):
        for bitPlane in bitPlanes:
            self.bitPlanePriorities[bitPlane.priority] = bitPlane
            
    def _sort_bit_planes(self):
        # Custom sorting key function
        def sort_key(bit_plane: Models.BitPlaneModel):
            subband_order = {"LL": 0, "HL": 1, "LH": 2, "HH": 3}
            return (-bit_plane.bitNum, -bit_plane.priority, -bit_plane.levelOfDecomp, subband_order[bit_plane.subband])

        # Sort the bit planes using the custom key function
        self.bitPlanes = sorted(self.bitPlanes, key=sort_key)
        
    def encode_bit_planes(self):
        # Implement the bit-plane encoding process
        # Encode the bit planes starting from MSB down to LSB
        self._sort_bit_planes()

        # Loop through each bitplane (where each bitplane is a numpy 2D array of pixels) in bitplanes
        for i in tqdm(range(len(self.bitPlanes))):
            bit_plane = self.bitPlanes[i]
            # Loop through each pixel in raster scan order (row by row)
            for row in range(bit_plane.bitPlaneMatrix.shape[0]):
                for col in range(bit_plane.bitPlaneMatrix.shape[1]):
                    # Get the current bit
                    current_bit = bit_plane.bitPlaneMatrix[row, col]
                    
                    # Get the current category
                    current_category = bit_plane.get_categories([(row, col)])[0]

                    # Get neighbors
                    neighbors = helpers.get_neighbors((row, col), bit_plane.bitPlaneMatrix)

                    # Get neighbor categories
                    for position, coordinates in neighbors.items():
                        position_categories = bit_plane.get_categories(coordinates)
                        significant_neighbors = np.count_nonzero(position_categories)
                        neighbors[position] = significant_neighbors
                    
                    # Get current context
                    current_context =helpers.determine_context(current_category, bit_plane.subband , neighbors)

                    # Update and set context
                    bit_plane.context.update_context(current_context, current_bit)
                    
                    # Update category
                    if current_bit == 1:
                        bit_plane.update_category((row, col), min([current_category + 1,3]))

                    # Send bit and context to entropy coder
                    # TODO: Implement entropy coder
                    # entropy_coder.encode(bit, bit_plane.context)
        print(self.bitPlanes[0].context.contexts)


            


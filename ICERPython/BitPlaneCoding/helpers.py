import numpy as np
from ICERPython.BitPlaneCoding.Models import BitPlaneModel
from ICERPython.BitPlaneCoding.Models import ContextModel

# Context helpers
def determine_context(pixel_category: int, subband: str, significant_neighbors: tuple[int, int, int]):
    # h, v, d = significant_neighbors
    h = significant_neighbors["horizontal"]
    v = significant_neighbors["vertical"]
    d = significant_neighbors["diagonal"]

    if pixel_category == 0:
        if subband == "HH":
            context = context_category0_HH(h, v, d)
        elif subband == "HL":
            # In HL subband, h and v are swapped
            context = context_category0_LL_LH_HL(v, h, d)
        else:
            context = context_category0_LL_LH_HL(h, v, d)
    elif pixel_category == 1:
        context = 9 if (h == 0 and v == 0) else 10
    elif pixel_category == 2:
        context = 11
    else:
        context = None

    return context

def context_category0_LL_LH_HL(h, v, d):
    if h == 0:
        if v == 0:
            if d == 0:
                return 0
            elif d == 1:
                return 1
            else:
                return 2
        elif v == 1:
            return 3
        else:
            return 4
    elif h == 1:
        if v == 0:
            return 5 if d == 0 else 6
        else:
            return 7
    else:
        return 8

def context_category0_HH(h, v, d):
    contexts = [[0, 1, 2], [3, 4, 5], [6, 7, 7], [8, 8, 8]]
    return contexts[min(d, 3)][min(h + v, 2)]

def determine_sign_context(subband, neighbors, sign_matrix):
    horizontal = sum(int(sign_matrix[coord]) for coord in neighbors["horizontal"])
    vertical = sum(int(sign_matrix[coord]) for coord in neighbors["vertical"])
    if subband == "HL":
        horizontal, vertical = vertical, horizontal
    horizontal = int(np.sign(horizontal))
    vertical = int(np.sign(vertical))
    contexts = [[16, 13, 14], [15, 12, 15], [14, 13, 16]]
    prediction = int(horizontal < 0 or (horizontal == 0 and vertical > 0))
    return contexts[vertical + 1][horizontal + 1], prediction

def bit_plane_sort_key(bit_plane):
    subband_order = {"LL": 0, "HL": 1, "LH": 2, "HH": 3}
    return (-bit_plane.priority, -bit_plane.levelOfDecomp, subband_order[bit_plane.subband])

def update_neighbor_counts(neighbors, neighbor_counts):
    for position, coordinates in neighbors.items():
        for coord in coordinates:
            neighbor_counts[position][coord] += 1

# Bit plane helpers
# get 8 neighbors of a pixel within a numpy array
def get_neighbors(pixel_coords: tuple[int, int], array: np.array):
    x, y = pixel_coords
    neighbors = {
                 "diagonal": [],
                 "horizontal": [],
                 "vertical": [],
                 }
    for i in range(-1, 2):
        for j in range(-1, 2):
            if (i == 0 and j == 0) or x+i < 0 or y+j < 0 or x+i >= array.shape[0] or y+j >= array.shape[1]:
                continue
            if i != 0 and j != 0:
                neighbors["diagonal"].append((x+i, y+j))
            elif i == 0:
                neighbors["horizontal"].append((x+i, y+j))
            else:
                neighbors["vertical"].append((x+i, y+j))
    return neighbors

def create_bitplane(array: np.array):
    bitplanes = {}
    magnitude = np.abs(np.asarray(array, dtype=np.int64))
    bit_count = max(1, int(magnitude.max()).bit_length()) if magnitude.size else 1
    for i in range(bit_count):
        bitplanes[i] = (magnitude >> i) & 1
    return bitplanes
    
    
def convert_to_signed_binary_helper(pixel_numpy: np.float64):
    pixel_int = int(pixel_numpy)
    
    return str(int(pixel_int < 0)) + bin(abs(pixel_int))[2:].zfill(7)

# construct bit plane models from decompLevels
def construct_bit_planes(decompLevels: dict[int, dict[str, np.array]]):
    bit_plane_models = []
    for level in decompLevels:
        for subband in decompLevels[level]:
            if decompLevels[level][subband] is None or decompLevels[level][subband].size == 0:
                continue
            # Get bit plane 2d numpy array for this subband
            bit_planes = create_bitplane(decompLevels[level][subband])
            # Create context model for this subband
            context_model = ContextModel.ContextModel()
            category_matrix = np.zeros(decompLevels[level][subband].shape, dtype=int)
            sign_matrix = np.sign(decompLevels[level][subband]).astype(int)
            # Create bit plane model for each bit plane
            for bitNum, bit_plane in bit_planes.items():
                if bit_plane is None:
                    continue
                
                bit_plane_models.append(BitPlaneModel.BitPlaneModel( \
                    level=level,
                    subband=subband,
                    bitNum=bitNum,
                    bitPlane=bit_plane,
                    context=context_model,
                    categoryMatrix=category_matrix,
                    signMatrix=sign_matrix))
            
            # bit_plane_models.append(BitPlaneModel.BitPlaneModel(level, subband, decompLevels[level][subband]))
    return bit_plane_models
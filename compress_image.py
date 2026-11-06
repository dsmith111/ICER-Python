from ICERPython.Wavelets import WaveletTransform as wt
from ICERPython.Wavelets import WaveletFilter as wf
from ICERPython.ICER import ICER
import numpy as np
import argparse
from PIL import Image
import os

global selected_filter

# Load image as grayscale
def load_image(path):
    # Load image from path
    with Image.open(path) as image:
        # Convert image to grayscale (black and white)
        image = image.convert('L')

        # Return image as a 2D numpy array
        return np.asarray(image)

def save_image(path, subbands):
    # Save the separate wavelet decomposed images
    # Create a directory based on the filter used
    path, file_name = os.path.split(path)
    path = os.path.join(path, selected_filter.filter_name)
    if not os.path.exists(path):
        os.makedirs(path)
    path = os.path.join(path, file_name)

    # Save images with names containing subband and level
    # subbands is a dictionary of the form {int: {str: np.array}}, e.x. {1: {"LL": np.array, "HL": np.array, "LH": np.array, "HH": np.array}}
    for level, subband in subbands.items():
        for subband_name, subband_image in subband.items():
            if subband_image is None or subband_image.size == 0:
                continue
            image = Image.fromarray(np.clip(subband_image, 0, 255).astype(np.uint8)).convert('L')
            image.save(path + f"_level{level}_{subband_name}.png")

def parse_args():
    parser = argparse.ArgumentParser(description='Compress an image with ICER.')
    parser.add_argument('-i', '--input_image', type=str, required=True, help='Path to input image or compressed file')
    parser.add_argument('-o', '--output_image', type=str, required=True, help='Output prefix, or reconstructed image path when decompressing')
    parser.add_argument('-l', '--levels', type=int, required = False, default=1, help='Number of levels of wavelet decomposition')
    parser.add_argument('-b', '--bitrate', type=float, required = False, default=0.5, help='Target bits per input pixel when using --lossy')
    parser.add_argument('-f', '--filter', type=str, required = False, default="A", help='Wavelet filter to use for compression')
    parser.add_argument('--filter_parameters', type=str, required = False, default=os.path.join(os.path.dirname(__file__), "filter_parameters.json"), help='Path to filter parameters file')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--lossless', action='store_true', help='Use lossless compression (default)')
    mode.add_argument('--lossy', action='store_true', help='Compress to a target bitrate')
    mode.add_argument('--decompress', action='store_true', help='Reconstruct an image from an ICER-Python compressed file')
    parser.add_argument('--minimum_loss', type=int, default=0, help='Minimum number of omitted level-1 HH bit planes')
    parser.add_argument('--byte_quota', type=int, help='Approximate entropy payload byte quota')
    parser.add_argument('--allow_partial', action='store_true', help='Decode a truncated entropy payload')
    parser.add_argument('--no_previews', action='store_true', help='Skip saving decomposed wavelet images')
    args = parser.parse_args()
    if args.lossless and (args.minimum_loss != 0 or args.byte_quota is not None):
        parser.error('--lossless cannot be combined with minimum loss or a byte quota')
    if args.allow_partial and not args.decompress:
        parser.error('--allow_partial requires --decompress')
    return args

if __name__ == "__main__":
    args = parse_args()
    # Define wavelet filter
    selected_filter = wf.WaveletFilter(args.filter, args.filter_parameters)

    if args.decompress:
        input_image = np.zeros((1, 1), dtype=int)
    else:
        # Load image as a grayscale numpy array
        input_image = load_image(args.input_image)
    
    # Select wavelet transform based on filter params
    wavelet_transform = wt.WaveletTransform(input_image, selected_filter)
    icer = ICER(wavelet_transform)
    
    os.makedirs(os.path.dirname(args.output_image) or '.', exist_ok=True)
    if args.decompress:
        with open(args.input_image, 'rb') as compressed_file:
            reconstructed_image = icer.decompression(compressed_file.read(), args.allow_partial)
        Image.fromarray(np.clip(reconstructed_image, 0, 255).astype(np.uint8)).save(args.output_image)
        print("Saved reconstructed image to " + args.output_image)
    else:
        if args.lossy or args.minimum_loss != 0 or args.byte_quota is not None:
            bitrate = args.bitrate if args.lossy else None
            subbands = icer.lossy_compression(bitrate, args.levels, args.minimum_loss, args.byte_quota)
        else:
            subbands = icer.lossless_compression(args.levels)
        compressed_path = args.output_image + '.icerpy'
        with open(compressed_path, 'wb') as compressed_file:
            compressed_file.write(icer.encoded_bit_stream)
        print("Saved compressed image to " + compressed_path)

        # Save decomposed images
        if not args.no_previews:
            save_image(args.output_image, subbands)

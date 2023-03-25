from ICERPython.Wavelets import WaveletTransform as wt
from ICERPython.Wavelets import WaveletFilter as wf
from ICERPython.ICER import ICER
import numpy as np
# Import argparse
import argparse
from PIL import Image
import os

global selected_filter

# Load image as grayscale
def load_image(path):
    # Load image from path
    image = Image.open(path)
    
    # Convert image to grayscale (black and white)
    image = image.convert('L')
    
    # Return image as a 2D numpy array
    return np.asarray(image)

def save_image(path, image):
    # Until the reconstruction is complete, we will save the separate wavelet decomposed images
    # Create a directory based on the filter used
    path, file_name = os.path.split(path)
    path = os.path.join(path, selected_filter.filter_name)
    if not os.path.exists(path):
        os.makedirs(path)
    path = os.path.join(path, file_name)

    # Save the low pass image
    low_pass_images = image[0]
    for index, decomposed_wavelet in enumerate(low_pass_images):
        low_pass_image = Image.fromarray(decomposed_wavelet).convert('L')
        low_pass_image.save(path + f"_low_pass{index}.png")
    
    # Save the high pass images
    high_pass_images = image[1]
    for index, decomposed_wavelet in enumerate(high_pass_images):
        high_pass_image = Image.fromarray(decomposed_wavelet).convert('L')
        high_pass_image.save(path + f"_high_pass{index}.png")

def parse_args():
    parser = argparse.ArgumentParser(description='Compress an image with ICER.')
    parser.add_argument('-i', '--input_image', type=str, help='Path to input image')
    parser.add_argument('-o', '--output_image', type=str, help='Path to output image')
    parser.add_argument('-b', '--bitrate', type=float, required = False, default=0.5, help='Bitrate for lossy compression')
    parser.add_argument('-f', '--filter', type=str, required = False, default="A", help='Wavelet filter to use for compression')
    parser.add_argument('--filter_parameters', type=str, required = False, default="./filter_parameters.json", help='Path to filter parameters file')
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    # Define wavelet filter
    selected_filter = wf.WaveletFilter(args.filter, args.filter_parameters)

    # Load image as a grayscale numpy array
    input_image = load_image(args.input_image)
    
    # Select wavelet transform based on filter params
    wavelet_transform = wt.WaveletTransform(input_image, selected_filter)
    icer = ICER(wavelet_transform)
    
    # We're only implementing lossless compression at first
    compressed_image = icer.lossless_compression()
    
    # Save decomposed images
    save_image(args.output_image, compressed_image)
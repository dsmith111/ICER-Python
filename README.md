# A Reference for Implementing Algorithms in Publications - ICER Image Compression via Wavelet Transformation

Unless their work incorporates research in some form, many software engineers, data scientists, developers won't know where to begin if they decide, or have to, translate a concept for some algorithm, architecture or other process from research papers to a fully functioning program. If you're not already experienced in the field behind a publication, they will come off as dense, jargon heavy and unreadable due to the general consensus from the authors that anyone reading the paper will be fully up to date with every concept that is not the topic of the paper (i.e. they are not self-contained). 

However, this is less of a problem when the reader is intending to implement the resource. This may sound counter-intuitive at first, but converting these concepts into programs requires breaking the concept down into implementable sub-components. From here, the reader can focus on understanding the concepts behind each of these components separately. This provides concrete direction on what needs to be researched, why it is needed for the program to function and how it'll eventually be implemented.

## What paper will be used?

In this repository, we will be going over the ["The ICER Progressive Wavelet Image Compressor"](https://ipnpr.jpl.nasa.gov/progress_report/42-155/155J.pdf) algorithm developed by NASA JPL.

## Why this paper?

This project will hopefully cover the process for handling large, complex publications and should be applicable to much lighter versions. The paper we're referencing is a hefty 46 pages (43 without references), utilizes distinct concepts and discusses the stages of the algorithm along with the theoretical foundations of these stages. 

# ICER Image Compression using Wavelet Transformation in Python

This repository will not only be acting as a guide or reference, but it will, of course, contain a fully implemented version of the algorithm and also contain the standard information in a GitHub repository to demonstrate both, the implementation and presentation of a translated algorithm.

## Background
At the time of development, the only available implementation of the ICER progressive wavelet image compression technique is in C. Of course, this is done in C with memory constraints in mind as this algorithm is originally for NASA exploration hardware. However, for readability, accesibility and modernity purposes, this version implements this technique in Python.

_Note: This is still a work in progress. Here is the task list:_

- [x] Step 1: Wavelet Transformations
  - [x] One-Dimensional Wavelet Transformation
    - [x] Low-pass Filter Implementation
    - [x] High-pass Filter Implementation
  - [x] Two-Dimensional Wavelet Transformation
    - [x] Multi-level Decomposition
- [x] Steps 2: Bit-Plane Coding
  - [x] Bit-Plane Construction
    - [x] Pixel Binarization
  - [x] Categorization
  - [x] Context Modelling
  - [x] Encoding Prioritzation
  - [ ] Encoding Optimization
- [ ] Step 3: Entropy Coding
- [ ] Step 4: Image Quality and Compression Controlling

## Quick Links
_Note: Equations are in LateX which does not display properly in the official GitHub mobile app_

- [How does Wavelet Transformation Work?](https://github.com/dsmith111/ICER-Python/blob/master/ICERPython/Wavelets/README.md)
- [How does Bit-plane Coding Work?](https://github.com/dsmith111/ICER-Python/blob/master/ICERPython/BitPlaneCoding/README.md)

## Installation
Clone the repository:

```bash
Copy code
git clone https://github.com/dsmith111/ICER-Python.git
cd ICER-Python
```

Install the required dependencies:
```bash
Copy code
pip install -r requirements.txt
```
## Usage
The main script for compressing images is compress_image.py. 

### Command Line Arguments

`compress_image.py` accepts the following command line arguments:

- `-i`, `--input_image`: Path to the input image file that you want to compress.
- `-o`, `--output_image`: Prefix for the output image files. The decomposed images will be saved with this prefix and an appropriate suffix, e.g., `_low_pass0.png` and `_high_pass0.png`.
- `-b`, `--bitrate`: (Optional) Bitrate for lossy compression. Default value is `0.5`.
- `-f`, `--filter`: (Optional) Wavelet filter to use for compression. Default value is `"A"`.
- `--filter_parameters`: (Optional) Path to the filter parameters JSON file. Default value is `"./filter_parameters.json"`.

#### Example Usage

To compress an image using the ICER algorithm with the default parameters, run the following command:

```bash
python3 compress_image.py -i path/to/input/image.jpg -o path/to/output/image_prefix -f A
```
This command will perform the wavelet transform on the input image, save the decomposed images as PNG files, and store them in the specified output path with the given prefix.

The decomposed images will have filenames like `image_prefix_low_pass0.png` and `image_prefix_high_pass0.png`.

_Note_: The current implementation only supports grayscale images.

## Project Structure
The project is organized into the following directories:

- `ICERPython`: Contains the main ICER algorithm implementation and the wavelet transform classes.
   - `Wavelets`: Contains the wavelet filter and transform classes, as well as the filters (low-pass and high-pass) used in the wavelet transform.
      - `WaveletFilter.py`
      - `WaveletTransform.py`
      - `Filters`: Contains the low-pass and high-pass filter classes.
         - `HighPassFilters.py`
         - `LowPassFilters.py`
   - `BitPlaneCoding`: Contains the classes and methods related to bit-plane coding.
      - `BitPlaneEncoder.py`: Implements the bit-plane encoding process.
      - `BitPlaneDecoder.py`: Implements the bit-plane decoding process.
      - `ContextModel.py`: Contains the context modeling methods for bit-plane coding.
      - `ProbabilityEstimation.py`: Contains the methods for probability estimation used in the entropy coding process.
   - `ICER.py`: Main ICER implementation, integrating all the components (Wavelets, BitPlaneCoding, etc.).


The main script for compressing images is `compress_image.py`.

## Results
### Wavelet Transformation
The first step in the ICER algorithm is the break down images based on wavelet decomposition. The major note here as to why this is important when compared to other compression algorithms is the full image data compression rather than performing compression region by region. In the event of data transmission failure, most images would simply not have a region of the image; in this case, we are setting up the rest of the algorithm to allow us to send much lower fidelity full images. This allows us to have a better guarantee of receiving a full image with the cost of fidelity incase of any failures.

Here is a comparison of this algorithm's decomposition vs the results in the paper:

#### Python ICER

**Original Image**

![](./original_images/rover.jpg)

**Decomposed Images**

Horizontal Low-pass, Vertical Low-pass   |  Horizontal Low-pass, Vertical High-pass
:-------------------------:|:-------------------------:
![](./decomposed_wavelets/A/rover_compressed_low_pass0.png)  |  ![](./decomposed_wavelets/A/rover_compressed_high_pass0.png)

### NASA ICER

**Original Image**

![](./assets/icer-rover.png)

**Decomposed Images**

Decomposed Images  |  Labels
:-------------------------:|:-------------------------:
![](./assets/icer-passes.png)  |  ![](./assets/icer-desc.png)

_These images were taken directly from the research paper, hence the lower resolution_

Comparing the Python ICER results against the original NASA ICER results, we can see the decomposition has been accurately implemented.

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

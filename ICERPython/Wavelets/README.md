# Wavelet Transformations and Filters

Here I'll touch a bit on the wavelet filters used in this image compression algorithm and then I'll summarize the way the filters are implemented.

## What are these Transformations for?

These filters are crucial for achieving efficient lossless and near-lossless compression. The filters are non-linear approximations to linear high-pass/low-pass filter pairs, and the nonlinearity arises from the use of roundoff operations.

The ICER algorithm should allow a user to utilize one of seven reversible integer wavelet transforms. These transforms produce integer outputs and are exactly invertible when the input consists of integers. The wavelet transforms are computed in essentially the same way but use different choices of filter coefficients.

## What are these Filters?
ICER provides seven types of filters, labeled as Filter A through F, and an additional filter called Filter Q. Filter A is essentially the same as the "Reversible Two-Six" transform, and the others are from the referenced literature.

### Filter Parameters
For each filter type, there are four filter parameters: α−1, α0, α1, and β. These parameters determine the behavior of the high-pass filter output.

The table below lists the filter parameters for each filter type:

_Table 1_

| Filter | α−1   | α0   | α1   | β    |
| ------ | ----- | ---- | ---- | ---- |
| A      | 0     | 1/4  | 1/4  | 0    |
| B      | 0     | 2/8  | 3/8  | 2/8  |
| C      | -1/16 | 4/16 | 8/16 | 6/16 |
| D      | 0     | 4/16 | 5/16 | 2/16 |
| E      | 0     | 3/16 | 8/16 | 6/16 |
| F      | 0     | 3/16 | 9/16 | 8/16 |
| Q      | 0     | 1/4  | 1/4  | 1/4  |

## How do these Filters work?
The `Filters` sub-directory contains the implementations of the low-pass and high-pass filters used in the wavelet transformation process utilzing the parameters described in table 1.

1. _Low-Pass Filter (LowPassFilters.py)_

The low-pass filter is responsible for smoothing the input data and preserving the low-frequency components. It takes an input data array and computes the output values as follows:

- For even-length data, it computes the first (N / 2) - 1 outputs using the average of the current data point and the next data point.
   
- For odd-length data, it computes the output values as for even-length data and sets the last output value as the last data point.

This follows the equation:

$$ l[n] = 
\begin{cases}
[\frac{1}{2}*(x[2n]+x[2n+1])] & n=0,1,...,[\frac{N}{2}] \\
x[N-1] & n=[\frac{N-1}{2}],N \space odd \\
\end{cases} $$

2. _High-Pass Filter (HighPassFilters.py)_

The high-pass filter is responsible for detecting the high-frequency components or rapid changes in the input data. It takes an input data array, the low-pass filter outputs, and filter parameters. The filter computes the following:

- d(n) values, which represent the difference between adjacent data points.

$$ d[n] = 
\begin{cases}
[x[2n]-x[2n+1]) & n=0,1,...,[\frac{N}{2}] \\
0 & n=[\frac{N-1}{2}],N \space odd \\
\end{cases} $$

- r(n) values, which represent the difference between adjacent low-pass filter outputs.

$$ r[n] = l[n-1] -l[n], n=1,2,...,[\frac{N}{2}] - 1$$

- High-pass filter outputs, which are computed based on the filter parameters and the computed d(n) and r(n) values.

The high-pass filter output computation varies depending on the current index value and the filter parameters. The implemented conditions cover different edge cases, such as the first and last output values and specific parameter configurations.

This follows the equation:

$$ h[n] = d[n] -
\begin{cases}
[\frac{1}{4}r[1]] & n=0 \\
[\frac{1}{4}r[1] + \frac{3}{8}r[2] - \frac{1}{4}d[2] + \frac{1}{2}] & n=1,a_{-1} \neq 0 \\
[\frac{1}{4}r[\frac{N}{2} - 1]] & N \text{ even}, n=\frac{N}{2}-1 \\
[\alpha_{-1} r[n-1] + \alpha_0 r[n] + \alpha_1 r[n+1] - \beta d[n+1] + \frac{1}{2}] & \text{otherwise}
\end{cases} $$


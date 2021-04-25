"""Function to get the vertices of a level set
"""

import numpy as np
import scipy.interpolate
import matplotlib.pyplot as plt
from toolz.curried import pipe, curry


@curry
def calc_contour_vertices(data, domain, fill_value, contour_value=0.0, n_interp=500):
    """Calculate a levelsets vertex positions on a 2D contour plot

    Args:
      data: unstructured (n, 3) array with x, y and z values
      domain: the size of the domain (assumed to be square currently)
      fill_value: the fill value for points that aren't covered by the
        interpolation.
      contour_value: the contour value to find
      n_interp: the number of points in the x and y direction for
        interpolation purposes

    >>> np.random.seed(99)
    >>> xy = 4 * np.random.random((1000, 2)) - 2
    >>> values = np.sqrt(np.sum(xy**2, axis=-1)) - 1
    >>> data = np.concatenate((xy, values[:, None]), axis=-1)
    >>> coords = calc_contour_vertices(data, fill_value=10, domain=[-2, 2])
    >>> values = np.sum(coords**2, axis=-1)
    >>> assert np.allclose(values, 1, rtol=1e-2)

    """
    interp = lambda x: scipy.interpolate.griddata(
        data[:, :2], data[:, 2], tuple(x), method="cubic", fill_value=fill_value
    )

    return pipe(
        np.linspace(domain[0], domain[1], n_interp),
        lambda x: np.meshgrid(x, x),
        lambda x: plt.contour(*x, interp(x), [contour_value, np.amax(data)]),
        lambda x: x.collections[0].get_paths()[0].vertices,
    )

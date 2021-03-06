import os
import cv2
import numpy as np
from datetime import datetime
from . import print_image
from . import plot_image
from . import apply_mask


def cluster_contour_splitimg(device, img, grouped_contour_indexes, contours, outdir=None, file=None,
                             filenames=None, debug=None):

    """
    This function takes clustered contours and splits them into multiple images, also does a check to make sure that
    the number of inputted filenames matches the number of clustered contours.

    Inputs:
    device                  = Counter for image processing steps
    img                     = ideally a masked RGB image.
    grouped_contour_indexes = output of cluster_contours, indexes of clusters of contours
    contours                = contours to cluster, output of cluster_contours
    outdir                  = out directory for output images
    file                    = the name of the input image to use as a base name,
                              output of filename from read_image function
    filenames               = input txt file with list of filenames in order from top to bottom left to right
                              (likely list of genotypes)
    debug                   = print debugging images

    Returns:
    device                  = pipeline step counter
    output_path             = array of paths to output images

    :param device: int
    :param img: ndarray
    :param grouped_contour_indexes: list
    :param contours: list
    :param outdir: str
    :param file: str
    :param filenames: str
    :param debug: str
    :return device: int
    :return output_path: str
    """

    # get names to split also to check the target number of objects

    i = datetime.now()
    timenow = i.strftime('%m-%d-%Y_%H:%M:%S')

    if file == None:
        filebase = timenow
    else:
        filebase = file[:-4]

    if filenames == None:
        l = len(grouped_contour_indexes)
        namelist = []
        for x in range(0, l):
            namelist.append(x)
    else:
        with open(filenames, 'r') as n:
            namelist = n.read().splitlines()
        n.close()

    # make sure the number of objects matches the namelist, and if not, remove the smallest grouped countor
    # removing contours is not ideal but the lists don't match there is a warning to check output

    if len(namelist) == len(grouped_contour_indexes):
        corrected_contour_indexes = grouped_contour_indexes
    elif len(namelist) < len(grouped_contour_indexes):
        print("Warning number of names is less than number of grouped contours, attempting to fix, to double check "
              "output")
        diff = len(grouped_contour_indexes) - len(namelist)
        size = []
        for i, x in enumerate(grouped_contour_indexes):
            totallen = []
            for a in x:
                g = i
                la = len(contours[a])
                totallen.append(la)
            sumlen = np.sum(totallen)
            size.append((sumlen, g, i))

        dtype = [('len', int), ('group', list), ('index', int)]
        lencontour = np.array(size, dtype=dtype)
        lencontour = np.sort(lencontour, order='len')

        rm_contour = lencontour[diff:]
        rm_contour = np.sort(rm_contour, order='group')
        corrected_contour_indexes = []

        for x in rm_contour:
            index = x[2]
            corrected_contour_indexes.append(grouped_contour_indexes[index])

    elif len(namelist) > len(grouped_contour_indexes):
        print("Warning number of names is more than number of  grouped contours, double check output")
        diff = len(namelist) - len(grouped_contour_indexes)
        namelist = namelist[0:-diff]
        corrected_contour_indexes = grouped_contour_indexes

    # create filenames

    group_names = []
    for i, x in enumerate(namelist):
        plantname = str(filebase) + '_' + str(x) + '_p' + str(i) + '.jpg'
        group_names.append(plantname)

    # split image

    output_path = []

    for y, x in enumerate(corrected_contour_indexes):
        if outdir != None:
            savename = os.path.join(str(outdir), group_names[y])
        else:
            savename = os.path.join(".", group_names[y])
        iy, ix, iz = np.shape(img)
        mask = np.zeros((iy, ix, 3), dtype=np.uint8)
        masked_img = np.copy(img)
        for a in x:
            cv2.drawContours(mask, contours, a, (255, 255, 255), -1, lineType=8)

        mask_binary = mask[:, :, 0]

        if np.sum(mask_binary) == 0:
            pass
        else:
            retval, mask_binary = cv2.threshold(mask_binary, 254, 255, cv2.THRESH_BINARY)
            device, masked1 = apply_mask(masked_img, mask_binary, 'white', device, debug)
            if outdir != None:
                print_image(masked1, savename)
            output_path.append(savename)

            if debug == 'print':
                print_image(masked1, (str(device) + '_clusters.png'))
            elif debug == 'plot':
                if len(np.shape(masked1)) == 3:
                    plot_image(masked1)
                else:
                    plot_image(masked1, cmap='gray')
                    plot_image(masked1)

    return device, output_path

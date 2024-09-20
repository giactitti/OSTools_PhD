# -*- coding: utf-8 -*-
"""
| ----------------------------------------------------------------------------------------------------------------------
| Date                : October 2020                                 todo: change date, copyright and email in all files
| Copyright           : © 2020 by Ann Crabbé
| Email               : acrabbe.foss@gmail.com
| Acknowledgements    : Based on 'Create A QGIS Plugin' [https://bitbucket.org/kul-reseco/create-qgis-plugin]
|                       Crabbé Ann and Somers Ben; funded by BELSPO STEREO III (Project LUMOS - SR/01/321)
|
| This file is part of the [INSERT PLUGIN NAME] plugin and [INSERT PYTHON PACKAGE NAME] python package.
| todo: make sure to fill out your plugin name and python package name here.
|
| This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public
| License as published by the Free Software Foundation, either version 3 of the License, or any later version.
|
| This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied
| warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more details.
|
| You should have received a copy of the GNU General Public License (COPYING.txt). If not see www.gnu.org/licenses.
| ----------------------------------------------------------------------------------------------------------------------
"""
import os
from osgeo import gdal,osr
gdal.UseExceptions()
gdal.SetConfigOption('CHECK_DISK_FREE_SPACE', 'FALSE')

# todo: this is the script where you gather functionality that is required in all interfaces, like importing an image


def import_image(path) -> tuple:
    """ Browse for an image and return it as numpy array.

    :param path: the absolute path to the image
    :return: float32 numpy array [#good bands x #rows x #columns] + metadata
    """

    if not os.path.exists(path):
        raise Exception("Cannot find file '" + path + "'.")

    try:
        data = gdal.Open(path)
        array = data.ReadAsArray()
        metadata = {'geo_transform': data.GetGeoTransform(), 'x_size': data.RasterXSize, 'y_size': data.RasterYSize,
                    'projection': data.GetProjection(),'src_srs': osr.SpatialReference(wkt=data.GetProjection()),'n_bands':data.RasterCount}

        return array, metadata

    except Exception as e:
        raise Exception(str(e))


def write_image(file_path, image, geo_transform=None, projection=None, gdal_type=gdal.GDT_Int16, n_bands=1):

    driver = gdal.GetDriverByName('GTiff')
    #n_bands = len(image)

    print(n_bands)

    if os.path.exists(file_path):
        os.remove(file_path)

    raster = driver.Create(file_path, image.shape[1], image.shape[0], n_bands, gdal_type)

    

    #for band, b in zip(image, range(1, n_bands+1)):
    #    raster.GetRasterBand(b).WriteArray(band)
    if n_bands==1:
        band=raster.GetRasterBand(1)
        band.WriteArray(image)
        band.SetNoDataValue(-9999)
    else:
        for i in range(n_bands):
            band=raster.GetRasterBand(i+1)
            band.WriteArray(image[:,:,i])
            band.SetNoDataValue(-9999)

    if geo_transform:
        raster.SetGeoTransform(geo_transform)
    if projection:
        raster.SetProjection(projection)
    raster.FlushCache()

    return file_path

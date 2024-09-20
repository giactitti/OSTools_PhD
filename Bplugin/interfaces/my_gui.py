# -*- coding: utf-8 -*-

import os
import os.path as op
import tempfile

from osgeo import gdal
from PyQt5.QtCore import Qt
from qgis.gui import QgsFileWidget
from qgis.core import QgsProviderRegistry, QgsMapLayerProxyModel, QgsRasterLayer, QgsProject
from qgis.PyQt.QtCore import QCoreApplication
from qgis.utils import iface
from qgis.PyQt.uic import loadUi
from qgis.PyQt.QtWidgets import QDialog, QFileDialog, QDialogButtonBox, QMessageBox

from Bplugin.core.my_code import MyCode
from Bplugin.utils import utils


class MyWidget(QDialog):
    def __init__(self):
        super(MyWidget, self).__init__()
        loadUi(op.join(op.dirname(__file__), 'my_gui.ui'), self)

        # input
        self.rasterDropDown.setCurrentIndex(-1)
        self.rasterDropDown.setFilters(QgsMapLayerProxyModel.RasterLayer)
        self.rasterDropDown.layerChanged.connect(self._choose_raster)
        self.imageAction.triggered.connect(self._browse_for_raster)
        self.rasterButton.setDefaultAction(self.imageAction)

        # output
        self.outputFileWidget.lineEdit().setReadOnly(True)
        self.outputFileWidget.lineEdit().setPlaceholderText('[Create temporary layer]')
        self.outputFileWidget.setStorageMode(QgsFileWidget.SaveFile)
        self.outputFileWidget.setFilter("Tiff (*.tif);;All (*.*)")

        # Open in QGIS?
        try:
            iface.activeLayer
        except AttributeError:
            self.openCheckBox.setChecked(False)
            self.openCheckBox.setDisabled(True)

        # run or cancel
        self.OKClose.button(QDialogButtonBox.Ok).setText("Run")
        self.OKClose.accepted.connect(self._run)
        self.OKClose.rejected.connect(self.close)

        # widget variables
        self.image = None
        self.classified = None

    def log(self, text):
        # append text to log window
        self.logBrowser.append(str(text) + '\n')
        # open the widget on the log screen
        self.tabWidget.setCurrentIndex(self.tabWidget.indexOf(self.tab_log))

    def _browse_for_raster(self):
        
        path = QFileDialog.getOpenFileName(filter=QgsProviderRegistry.instance().fileRasterFilters())[0]

        try:
            if len(path) > 0:
                gdal.UseExceptions()
                layer = QgsRasterLayer(path, os.path.splitext(op.basename(path))[0])
                assert layer.isValid()
                QgsProject.instance().addMapLayer(layer, True)

                self.rasterDropDown.setLayer(layer)

        except AssertionError:
            self.log("'" + path + "' not recognized as a supported file format.")
        except Exception as e:
            self.log(e)

    def _choose_raster(self):

        layer = self.rasterDropDown.currentLayer()

        if layer is None:
            return
        try:
            print('loaded')

        except Exception as e:
            self.log(e)
           
    def _run(self):

        if not self.rasterDropDown.currentLayer():
            message = QCoreApplication.translate('Message to user','Please select input raster') 
            QMessageBox.warning(None, QCoreApplication.translate('Message to user', 'Missing Information'), message)
            return False
        else:
            output_path = self.outputFileWidget.filePath()

            if not self.openCheckBox.isChecked() and len(output_path) == 0:
                raise Exception("If you won't open the result in QGIS, you must select a base file name for output.")

            # Get parameters
            raster_path = self.rasterDropDown.currentLayer().source()
            rlayer = utils.import_raster(raster_path)

            # write image to file
            if len(output_path) == 0:
                output_path = op.join(tempfile.gettempdir(), 'outputRaster.tif')

            self.progressBar.setValue(0)
            
            # run code
            result = MyCode(rlayer,output_path).execute()

            # Open result in QGIS
            if self.openCheckBox.isChecked():
                QgsProject.instance().addMapLayer(result, True)

            self.progressBar.setValue(100)



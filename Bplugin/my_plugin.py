# -*- coding: utf-8 -*-

import os
from os import path

from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QMenu
from qgis.core import QgsApplication

# todo: import your own GUI or PROVIDER:
from Bplugin.interfaces.my_gui import MyWidget
#from qginla.interfaces.my_plugin_provider import MyProcessingProvider
from Bplugin.images.cqp_resources_rc import qInitResources
qInitResources()  # necessary to be able to access your images

#
# il plugin dovrà caricare un raster, calcolare la slope, filtrare tutti i valori sotto i 10 gradi con riga di comado
#


class MyPlugin:
    """ QGIS Plugin Implementation """

    def __init__(self, iface):

        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = path.dirname(__file__)

        # Add an empty menu to the toolbar
        self.toolbar = self.iface.addToolBar('Bplugin')
        self.toolbar.setObjectName('toolbar_Bplugin')

        # Add an empty menu to the plugin Menu
        self.main_menu = QMenu(title='Bplugin', parent=self.iface.pluginMenu())
        self.main_menu.setIcon(QIcon(':/Bplugin_logo'))
        self.iface.pluginMenu().addMenu(self.main_menu)
        self.provider = None

    def initGui(self):

        # add action button to toolbar
        action_toolbar = QAction(self.toolbar)
        action_toolbar.setText("Bplugin")
        action_toolbar.setIcon(QIcon(':/Bplugin_logo'))
        action_toolbar.triggered.connect(self.run_widget)

        self.toolbar.addAction(action_toolbar)

        # add action button to plugin menu
        action = QAction(QIcon(':/Bplugin_logo'), 'Bplugin', self.iface.mainWindow())
        action.triggered.connect(self.run_widget)
        action.setStatusTip('Quick information on your plugin.')
        
        self.main_menu.addAction(action)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        self.iface.rasterMenu().removeAction(self.main_menu.menuAction())

    @staticmethod
    def run_widget():
        widget = MyWidget()
        widget.show()
        widget.exec_()

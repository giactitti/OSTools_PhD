# -*- coding: utf-8 -*-

"""
/***************************************************************************
 ostools
                                 A QGIS plugin
 ciao
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2025-07-09
        copyright            : (C) 2025 by unibo
        email                : gianluca.lelli2@unibo.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'unibo'
__date__ = '2025-07-09'
__copyright__ = '(C) 2025 by unibo'

# This will get replaced with a git SHA1 when you do a git archive

__revision__ = '$Format:%H$'

from qgis.core import QgsProcessingProvider
from .scripts.catch import tc
from .scripts.basins_classification import Basins_classification_with_categorical_shape
from .scripts.Plugin_Code import Model
from .scripts.TemperatureStatistics import Modello2
from .scripts.Calcolo_precipitazione_media_areale import Grid_prec_erg5
from .scripts.Comp_RER import Comp_RER
from .scripts.Map import Xartis
from .scripts.multiple_clip import Multiple_clip

class ostoolsProvider(QgsProcessingProvider):

    def __init__(self):
        """
        Default constructor.
        """
        QgsProcessingProvider.__init__(self)

    def unload(self):
        """
        Unloads the provider. Any tear-down steps required by the provider
        should be implemented here.
        """
        pass

    def loadAlgorithms(self):
        """
        Loads all algorithms belonging to this provider.
        """
        self.addAlgorithm(tc())
        self.addAlgorithm(Basins_classification_with_categorical_shape())
        self.addAlgorithm(Model())
        self.addAlgorithm(Modello2())
        self.addAlgorithm(Grid_prec_erg5())
        self.addAlgorithm(Comp_RER())
        self.addAlgorithm(Xartis())
        self.addAlgorithm(Multiple_clip())
        # add additional algorithms here
        # self.addAlgorithm(MyOtherAlgorithm())

    def id(self):
        return 'os2025'

    def name(self):
        return self.tr('ostools2025')

    def icon(self):
        return QgsProcessingProvider.icon(self)

    def longName(self):
        return self.name()

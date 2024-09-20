# -*- coding: utf-8 -*-
from qgis.core import QgsProject

class MyCode:

    def __init__(self, rlayer,output):
        self.rlayer = rlayer
        self.output = output
        
    def execute(self):
        outlayer=self.rlayer
        print('output path:',self.output)
        return outlayer
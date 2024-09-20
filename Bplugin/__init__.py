# -*- coding: utf-8 -*-

def classFactory(iface):
   
    from Bplugin.my_plugin import MyPlugin
    return MyPlugin(iface)

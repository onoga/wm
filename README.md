# wm

INSTALLATION

1) Checkout wm  
2) Checkout toolib to wm/src  
3) Install webkit  

to Webware\WebKit\Configs\Application.config  

add line    
Contexts['wm'] = 'c:\\projects\\wm\\wkroot'  

change settings  
SessionStore = 'Memory' # can be File, Dynamic, Memcached, Memory or Shelve  
ExtraPathInfo = False # no extra path info  

4) Install python 2.7 and python modules  

setuptools  
PIL  
simplejson  
pywin32  
comtypes  
wxPython-2.8.10.1-unicode-gridfix.win32-py2.7.exe  
wxPython-common-2.8.10.1-unicode-gridfix.win32.exe  


# wm

INSTALLATION

1. Checkout wm
2. Checkout toolib to wm/src
3. Install webkit

to Webware\WebKit\Configs\Application.config 

add line 
Contexts['wm'] = 'c:\\projects\\wm\\wkroot'

change settings
SessionStore = 'Memory' # can be File, Dynamic, Memcached, Memory or Shelve
ExtraPathInfo = False # no extra path info

4. Instsall python 2.7 and python modules

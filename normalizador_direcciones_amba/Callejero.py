# coding: UTF-8
'''
Created on Apr 21, 2014

@author: hernan
'''
 
import urllib2, urllib, re, unicodedata
import simplejson as json
from Calle import Calle
from bisect import bisect_left

from settings import *
from commons import *

class Callejero:
    '''
    @cvar server: URL del servidor de datos de calles. Tiene un valor por defecto.
    @type server: String 
    @cvar data: La base de datos del callejero [id_calle, nombre_calle, keywords, array_de_rango_de_alturas, array_de_cruces]
    @type data: Array
    @cvar osm_ids: Array con los osm ids de calle para la busqueda binaria [id_calle]
    @type osm_ids: Array
    @ivar partido: Partido de la direccion
    @type partido: Partido
    '''
    server = ''
    data = []
    osm_ids = []
    partido = None
    
    # Minicache [calle, opts]
    # calle: la calle ingresada por parametro a matcheaCalle
    # opts: el resultado que devuelve
    minicache = ['gslgimigawakaranaigslg',[]]
    
    def __init__(self, partido):
        '''
        Carga el callejero
        '''
        try:
            self.partido = partido
            self.server = '{0}callejero/?partido={1}'.format(CALLEJERO_AMBA_SERVER, partido.codigo)
            self.cargarCallejero()
        except Exception, e:
            raise e

    def cargarCallejero(self):
        '''
        Carga las calles en el atributo data sin los cruces 
        '''
        try:
            data = urllib2.urlopen(self.server).read()
            self.data = json.loads(data, "utf8")
            for d in self.data:
                d.append(set(normalizarTexto(d[1], separador=' ', lower=False).split(' ')))
            self.data.sort() # Ordeno por id
            self.osm_ids = [k[0] for k in self.data] # Armo lista de osm_ids
        except urllib2.HTTPError, e:
            e.detalle = 'Se produjo un error al intentar cargar la información de calles.'
            raise e
        except Exception, e:
            raise e

    def buscarCodigo(self, codigo):
        '''
        Busca calle por codigo y devuelve una instancia de Calle
        @param codigo: Codigo de calle
        @type calle: Int
        @return: instancias de Calle
        @rtype: Calle
        '''
        pos = bisect_left(self.osm_ids, codigo)
        if pos < len(self.data) and self.data[pos][0] == codigo:
            return self.data[pos]
        else:
            return None
        
    def buscarCalle(self, calle, limit=0):
        '''
        Busca calles cuyo nombre se corresponda con calle y devuelve un array con todas las instancias de Calle halladas
        @param calle: String a matchear
        @type calle: String
        @param limit: Maximo numero de respuestas a devolver. Cero es sin limite.
        @type limit: Integer
        @return: Array de instancias de Calle que matchearon calle
        @rtype: Array de Calle 
        '''

        if self.minicache[0] == calle:
            return self.minicache[1] if limit == 0 else self.minicache[1][:limit]
        
        res = [[],[],[],[]]
        calleNorm1 = normalizarTexto(calle, separador=' ', lower=False)
        words1 = list(set(calleNorm1.split(' ')))
        words1.sort(key=len, reverse=True)
        regexps1 = map(lambda x: re.compile(ur'^{0}| {1}'.format(re.escape(x), re.escape(x))), words1)
        
        words1 = set(words1)
## No utilizo commons.matcheaTexto por cuestiones de optimizacion
## No podo la busqueda en limit para buscar las mejores soluciones
        for data in self.data:
            if calle == data[1]: # Match exacto con el nombre
                res[0].append(Calle(data[0], data[1], data[3], data[4], self.partido, data[5]))
            else: # Match permutado con el nombre
                if (words1 == data[6]):
                    res[1].append(Calle(data[0], data[1], data[3], data[4], self.partido, data[5]))
                elif (words1 == words1 & data[6]): # Match incluido con el nombre
                        res[2].append(Calle(data[0], data[1], data[3], data[4], self.partido, data[5]))
                else: # Match con las keywords de la calle
                    match = True
                    for regexp in regexps1:
                        if regexp.search(data[2]) == None:
                            match = False
                            break
                    if match:
                        res[3].append(Calle(data[0], data[1], data[3], data[4], self.partido, data[5]))
        
        res = res[0]+res[1]+res[2]+res[3]
        self.minicache = [calle, res]

        return res if limit == 0 else res[:limit] 

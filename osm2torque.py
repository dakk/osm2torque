#!/usr/bin/python
import math
import sys
import xml.etree.ElementTree

"""
new SimGroup(MissionGroup) {
   canSave = "1";
   canSaveDynamicFields = "1";
      enabled = "1";
"""

"""
 <way id="27920256" visible="true" version="1" changeset="508154" timestamp="2008-10-22T20:36:09Z" user="dmgroom" uid="1164">
  <nd ref="306485464"/>
  <nd ref="306485441"/>
  <nd ref="306485465"/>
  <nd ref="306485463"/>
  <nd ref="306485432"/>
  <tag k="highway" v="unclassified"/>
  <tag k="source" v="Yaho imagery"/>
 </way>
"""

"""
   new DecalRoad() {
      Material = "DefaultDecalRoadMaterial";
      textureLength = "5";
      breakAngle = "3";
      renderPriority = "10";
      position = "9.80889 2.39879 240.942";
      rotation = "1 0 0 0";
      scale = "1 1 1";
      canSave = "1";
      canSaveDynamicFields = "1";

      Node = "9.808894 2.398789 240.942383 10.000000";
      Node = "19.435331 -12.021607 242.012695 10.000000";
   };
"""


class TransverseMercator:
    radius = 6378137

    def __init__(self, **kwargs):
        # setting default values
        self.lat = 0 # in degrees
        self.lon = 0 # in degrees
        self.k = 1 # scale factor
        
        for attr in kwargs:
            setattr(self, attr, kwargs[attr])
        self.latInRadians = math.radians(self.lat)

    def fromGeographic(self, lat, lon):
        lat = math.radians(lat)
        lon = math.radians(lon-self.lon)
        B = math.sin(lon) * math.cos(lat)
        x = 0.5 * self.k * self.radius * math.log((1+B)/(1-B))
        y = self.k * self.radius * ( math.atan(math.tan(lat)/math.cos(lon)) - self.latInRadians )
        return (x,y)

    def toGeographic(self, x, y):
        x = x/(self.k * self.radius)
        y = y/(self.k * self.radius)
        D = y + self.latInRadians
        lon = math.atan(math.sinh(x)/math.cos(D))
        lat = math.asin(math.sin(D)/math.cosh(x))

        lon = self.lon + math.degrees(lon)
        lat = math.degrees(lat)
        return (lat, lon)
        


class OSM2Torque:
	# Translate Highway way type to torque materials
	MATERIALS = {
		"path": "Mat_road_asphalt_stripes_01",
		"primary": "Mat_road_asphalt_stripes_01",
		"secondary": "Mat_road_asphalt_stripes_01",
		"tertiary": "Mat_road_asphalt_stripes_01",
		"unclassified": "Mat_road_asphalt_stripes_01"
	}

	def __init__ (self, osmpath):
		self.mis = {
			"roads": []
		}
		self.osmpath = osmpath
		
	def load (self):
		self.osm = {
			"bounds": {},
			"nodes": {},
			"highways": []
		}

		e = xml.etree.ElementTree.parse (self.osmpath)
		
		# Boundary
		for b in e.findall ('bounds'):
			self.osm['bounds'] = { 'minlat': b.get ('minlat'), 'minlon': b.get ('minlon'), 'maxlat': b.get ('maxlat'), 'maxlon': b.get ('maxlon') }
			lat = (float (b.get ('minlat')) + float (b.get ('maxlat')))/2
			lon = (float (b.get ('minlon')) + float (b.get ('maxlon')))/2
			self.projection = TransverseMercator(lat=lat, lon=lon)
		
		# Add all nodes
		for n in e.findall('node'):
			if n.get ('visible') == 'true':
				self.osm['nodes'][n.get ('id')] = { 'lat': float (n.get ('lat')), 'lon': float (n.get ('lon')) }
	
		# For all ways where
		for w in e.findall('way'):
			if w.get ('visible') == 'true':
				# Get tags
				tags = {}
				for t in w.findall ('tag'):
					tags [t.get ('k')] = t.get ('v')

				# Parse highways					
				if 'highway' in tags:
					hw = { 'type': tags['highway'], 'nodes': [] }
					for nd in w.findall ('nd'):
						hw['nodes'].append (nd.get ('ref'))
						
					self.osm['highways'].append (hw)				
	
	
		
		
		
	def _generateRoad (self, hw):
		if not hw['type'] in self.MATERIALS:
			return None
			
		data = 'new DecalRoad() {\n'
		data += '\tMaterial = "' + self.MATERIALS[hw['type']] + '";\n'
		data += '\ttextureLength = "5";\n'
		data += '\tbreakAngle = "3";\n'
		data += '\trenderPriority = "10";\n'
		data += '\tposition = "0 0 2";\n'
		data += '\trotation = "1 0 0 0";\n'
		data += '\tscale = "1 1 1";\n'
		data += '\tcanSave = "1";\n'
		data += '\tcanSaveDynamicFields = "1";\n\n'

		for nd in hw['nodes']:
			node = self.osm['nodes'][nd]
			lat,lon = self.projection.fromGeographic (node['lat'], node['lon'])
			data += '\tNode = "' + str (lat) + ' ' + str (lon) + ' 2.000000 10.000000";\n'

		data += "};\n\n"
		return data		
		
		
	def loadTerrain (self):
		pass
		
	def generateTerrain (self):
		pass
			
	def generateRoads (self):
		for hw in self.osm['highways']:
			r = self._generateRoad (hw) 
			if r:
				self.mis['roads'].append (r)
			
	def save (self, outpath):
		f = open (outpath, 'w')
		for x in self.mis ['roads']:
			f.write (x)
		f.close ()

if __name__ == "__main__":
	if len (sys.argv) < 3:
		print "usage: python osm2torque.py file.osm level.mis"
		sys.exit (0)
		
	osmpath = sys.argv[1]
	outpath = sys.argv[2]
	ot = OSM2Torque (osmpath)
	ot.load ()
	ot.loadTerrain ()
	
	ot.generateTerrain ()
	ot.generateRoads ()
	ot.save (outpath)

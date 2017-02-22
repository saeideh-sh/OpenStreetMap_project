import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json
import dateutil.parser as parser
OSMFILE = "san-francisco_test1.osm"
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\-\_\. \t\r\n]')
amenity_correction_re = re.compile(r'(_)', re.IGNORECASE)
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
street_first_w_re = re.compile(r'^(St.|st.|St|st|N|N.|S|S.|s.|)\s')
name_correction_re = re.compile(r'(;)| (&amp;)| (&)', re.IGNORECASE)
county_correction_re = re.compile(r'(,)|CA', re.IGNORECASE)

mapping = { "St": "Street", "st":"Street", "St #": "Street #",
            "St.": "Street",
            "Ave": "Avenue","ave":"Avenue",
            "Ave." : "Avenue", "AVE":"Avenue", "avenue":"Avenue",
            'Rd.':"Road", "Rd": "Road" ,"N.": "North", "Blvd.": "Boulevard", "Blvd":"Boulevard",
            "Ln.":"Lane", "Plz.": "Plaza", "Plz": "Plaza", "S.":"South", "N":"North", "S":"South"}
first_match= {"St ": "Saint ", "St. ":"Saint ", "N. ": "North " , "S. ":"South ", "N ":"North ", "S ":"South "}

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]
#########Update_street_name#####################
def update_street_name(name, mapping):
    #search for the last words in the string
    m = street_type_re.search(name)

    better_name = name

    if name.find('#')!=-1:

        better_street_type = mapping["St #"]
        ## replace better_street_type in name
        better_name = name.replace("St #",better_street_type)
    else:
        if m :
            if m.group() in mapping.keys()  :

                better_street_type = mapping[m.group()]
                ## replace better_street_type in name
                better_name = street_type_re.sub(better_street_type, name)

    return better_name
def update_street_first_w(name, first_match):

    d = street_first_w_re.search(name)
    better_name = name
     #print "hi"
    if d:
        if d.group() in first_match.keys() :
            print d.group()
            better_first = first_match[d.group()]
            better_name = street_first_w_re.sub(better_first, name)

    return better_name
def improve_street(name):
    better_name = update_street_name(name, mapping)
    better_name = update_street_first_w(better_name,first_match)
    return better_name
###########################update_amenity##############
def update_amenity(name):
    m = amenity_correction_re.search(name)
    better_name = name
    if m :
        better_name = amenity_correction_re.sub(" ", better_name)
    return better_name
def name_char (name):
    better_name = name
    if better_name.find("(")!=-1:
        point = better_name.find("(")
        better_name = better_name[:(point-1)]
    elif better_name.find("[")!=-1:
        point = better_name.find("[")
        better_name = better_name[:(point-1)]
    elif better_name.find(":")!=-1:
        point = better_name.find(":")
        better_name = better_name[:(point)]
    return better_name
def improve_amenity(name):
    better_name = update_amenity(name)
    better_name = name_char (better_name)
    return better_name
######################## Update_name###################

def update_name(name):
    m = name_correction_re.search(name)
    better_name = name
    if m :
        better_name = name_correction_re.sub(" and", better_name)
    return better_name
def improve_name(name):
    better_name = update_name(name)
    better_name = name_char (better_name)
    return name
####################update_county*************
def name_char_county (name):

    m = county_correction_re.search(name)
    better_name = name
    if m :
        better_name = county_correction_re.sub("", better_name)
    return better_name


def improve_county(name):
    better_name = name_char_county(name)
    return better_name
###### date conversion

def parse_dict_date (date):
    total = dict()
    total["year"] = parser.parse(date).year
    total["month"] = parser.parse(date).month
    total["day"] = parser.parse(date).day
    return total



def shape_element(element):
    node = {}
    if element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        created={}
        ## e = adictionary of first line and its attribute
        for e in element.attrib.keys():

            if e in CREATED:
                if e == "timestamp":
                    created["timestamp"] = parse_dict_date(element.attrib[e])

                else:
                    created[e] = element.attrib[e]

            elif element.attrib[e] == element.get("lat") or element.attrib[e] == element.get("lon"):
                pos = []
                pos.append(float(element.attrib["lat"]))
                pos.append(float(element.attrib["lon"]))
                node["pos"] = pos
            else:# koja yan
                ## all attributes of "node" and "way" should be turned into regular key/value pairs
                node[e] = element.get(e)
            node["created"] = created
            node["type"] = element.tag
######################
        address={}
        node_refs=[]
        way ={}
        building={}
        for sub in element:
            if sub.tag == "tag":
                if re.search(problemchars, sub.get("k")):
                    continue
                elif sub.get("k")=="name":
                    node["name"] = improve_name(sub.attrib["v"])
                elif sub.get("k").startswith("addr:"):
                    if sub.get("k")== "addr:street":
                        address[sub.get("k")[5:]] = improve_street(sub.attrib["v"])
                    elif sub.get("k")== "addr:county":
                        address[sub.get("k")[5:]] = improve_county(sub.attrib["v"])
                    else:
                        address[sub.get("k")[5:]] = sub.attrib["v"]

                elif sub.get("k")=="building":
                    building[sub.get("k")] = sub.attrib["v"]
                elif sub.get("k").startswith("building:"):
                    #if sub.get("k")== "building:levels":
                    building[sub.get("k")[9:]] =sub.attrib["v"]
                    #else:
                        #building[sub.get("k")[9:]] =sub.attrib["v"]
                #     else:
                #         building[sub.get("k")] =

                elif sub.get("k") == "highway":
                    way["highway"]= sub.attrib["v"]
                elif sub.get("k") == "maxspeed":
                    way[sub.get("k")] = sub.attrib["v"]
                elif sub.get("k")=="lanes" :
                    way[sub.get("k")] = sub.attrib["v"]
                elif sub.get("k")=="sidewalk":
                    way[sub.get("k")] = sub.attrib["v"]
                elif sub.get("k").startswith("tiger:"):
                    if sub.get("k")=="tiger:county":
                        node[sub.get("k")[5:]] = improve_county(sub.attrib["v"])
                    else:
                        node[sub.get("k")[5:]] = (sub.attrib["v"])
                elif sub.get("k")== "amenity":
                    node[sub.get("k")] = improve_amenity(sub.attrib["v"])
                else:
                    node[sub.get("k")] = sub.attrib["v"]
            if sub.tag == "nd":
                node_refs.append(sub.attrib["ref"])

            if address:
                node["address"] = address
            if node_refs:
                node["node_refs"] =  node_refs
            if way:
                node["way"] = way
            if building:
                node["building"] = building
        #print node
        return node
    else:
        return None

def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    return data


data = process_map(OSMFILE, True)

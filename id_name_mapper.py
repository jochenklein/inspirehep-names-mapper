"""Collection of functions to map INSPIRE-IDs to INSPIRE-names.

Harvest INSPIRE-HEP names, map INSPIRE-IDs to INSPIRE-names, and write the
dictionary to a JSON file.

Usage:
    inspire_records = get_records()
    inspire_mapping = get_mapping(inspire_records)
    write_to_json(inspire_mapping, "<path/to/file.json>")
"""

import json
import os
import time
import urllib2
import xml.etree.ElementTree as ET

ns = {"x": "http://www.loc.gov/MARC21/slim"}  # XML namespaces


def get_records(record_limit=250):
    """Get MARCXML record elements.

    :param int record_limit: records limit each request. Maximum 251,
        except if you are a superadmin
    :return: list of MARCXML record elements or empty list
    """
    counter = 1
    records_all = []

    url = (
        "https://inspirehep.net/search?cc=HepNames"
        "&p=035__9%3ABAI+035__%3AINSPIRE&of=xm&ot=035&rg={0}&jrec={1}")

    while 1:
        req = urllib2.Request(url.format(record_limit, counter))
        try:
            response = urllib2.urlopen(req)
        except urllib2.URLError as e:
            print e.reason
        page_result = response.read()
        root = ET.fromstring(page_result)
        records = root.findall(".//x:record", namespaces=ns) or []

        if not records:
            break

        records_all = records_all + records
        counter += record_limit

        # Sleep some seconds between every request not to be banned
        time.sleep(3)

    return records_all


def get_mapping(inspire_records):
    """Get mapping INSPIRE-ID to INSPIRE-name.

    :param list inspire_records: list of MARCXML record elements
    :return: dictionary containing the mapping 'INSPIRE-ID: INSPIRE-name'.
        Example: {"INSPIRE-12345": "john.1", ...}
    """
    inspire_mapping = {}

    for record in inspire_records:
        inspire_id = inspire_name = None

        datafields = record.findall("x:datafield[@tag='035']", namespaces=ns)
        for datafield in datafields:
            subfield = datafield.find("x:subfield[@code='9']", namespaces=ns)
            if subfield is not None:
                subfield_a = datafield.find(
                    "x:subfield[@code='a']", namespaces=ns)
                if subfield_a is not None:
                    if (subfield.text == "INSPIRE"):
                        inspire_id = subfield_a.text
                    elif (subfield.text == "BAI"):
                        inspire_name = subfield_a.text

        inspire_mapping[inspire_id] = inspire_name

    return inspire_mapping


def write_to_json(inspire_mapping, dst):
    """Write inspire_mapping to dst using json.dump.

    :param dictionary inspire_mapping: INSPIRE-names mapping
    :param file dst: JSON file
    """
    directory = os.path.dirname(dst)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)

    try:
        with open(dst, "w") as f:
            try:
                json.dump(inspire_mapping, f)
            except ValueError as e:
                raise e
    except EnvironmentError as e:
        raise e

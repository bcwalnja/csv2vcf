import os
import re
import sys
import csv
import json
import unidecode
from optparse import OptionParser

input_file = "..\contacts2.csv"
output_dir = ".\output"
index_file = "index.json"
vcard_prop_file = "vcard.json"


class Csv:
    def __init__(self, value_list, name_to_index_dict):
        #get prop names from vcard.json
        prop_names = json.loads(open(vcard_prop_file).read())
        tmp = {
            propname: value_list[name_to_index_dict[propname]]
            for propname in prop_names
            if propname in name_to_index_dict
        }
        self.name_to_value_dict = {
            k: v for k, v in tmp.items() if v is not None
        }

        #if the name has a space in it, take the last word as the sname
        #and the rest as the fname
        #else if it doesn't have a space, take the whole thing as the fname
        #and leave the sname blank
        fn = self.name_to_value_dict.get("fn", "")
        if " " in fn:
            words = fn.split(" ")
            sname, fname = words[-1], " ".join(words[:-1])
            sname = sname.capitalize()
            fname = fname.capitalize()
        else:
            fname = fn.capitalize()
            sname = ""
        
        self.name_to_value_dict["n"] = "{sname};{fname};;;".format(
            sname=sname,
            fname=fname,
            **self.name_to_value_dict
        )

    def __str__(self):
        prop_names = json.loads(open(vcard_prop_file).read())
        prop_fmt_dict = {
            propname: "{propname}:{propvalue}"
            for propname in prop_names
        }
        res = ['BEGIN:VCARD', 'VERSION:3.0', 'CALSCALE=gregorian']
        res.append('KIND:individual')
        for propname, propvalue in self.name_to_value_dict.items():
            res.append(prop_fmt_dict[propname].format(
                propname=propname.upper(),
                propvalue=propvalue,
                **self.name_to_value_dict
            ))
        res.append("UID:{:d}".format(
            abs(hash(
                "would you like some salt?"+"".join(res))
            ))
        )
        res.append('END:VCARD')
        return "\n".join(res)

    def file_name(self):
        filename = self.name_to_value_dict["fn"].replace(" ", "_")
        filename += ".vcf"
        filename = filename.lower()
        return unidecode.unidecode(filename)


def csv_to_contacts_array(input_file, input_file_format):
    prop_names = json.loads(open(vcard_prop_file).read())
    index_to_name_dict = {prop_name: None for prop_name in prop_names}
    for propname in prop_names:
        index_to_name_dict[propname] = input_file_format.get(propname, None)
    with open(input_file, 'r') as source_file:
        reader = csv.reader(source_file)
        contacts_array = []
        for row in reader:
            contact = Csv(row, input_file_format)
            contacts_array.append(contact)
    return contacts_array


if __name__ == '__main__':
    conf_fmt = "  - Data for {value[fn]} written to {filename}"
    parser = OptionParser()
    (options, args) = parser.parse_args()
    
    if input_file == "":
        if len(args) < 1:
            error_msg = "No input file specified"
            raise Exception(error_msg)
        input_file = args[0]
    if output_dir == "":
        if len(args) < 2:
            error_msg = "No output directory specified"
            raise Exception(error_msg)
        output_dir = args[1]
    
    # get json from index.json
    # jsonInput = '{ "fn": 0, "email": 2, "tel": 3, "categories": 1 }'
    jsonInput = open('index.json').read()
    input_file_format = json.loads(jsonInput)
    if not os.path.isdir(output_dir):
        error_msg = "{} is not a directory".format(output_dir)
        raise Exception(error_msg)
    print("Creating files under {output_dir}".format(output_dir=output_dir))
    contacts_array = csv_to_contacts_array(input_file, input_file_format)
    for contact in contacts_array:
        filename = contact.file_name()

        illegal = '[\\/:"*?<>|]+'
        filename = re.sub(illegal, '', filename)

        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w") as f:
            f.write(str(contact))
            print(conf_fmt.format(
                value=contact.name_to_value_dict,
                filename = filename
            ))

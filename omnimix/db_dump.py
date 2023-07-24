import argparse
import os

from lxml.etree import tostring
from lxml.builder import E

import popndll


def save_databases(databases, output_base_folder):
    os.makedirs(output_base_folder, exist_ok=True)

    for data, elm_name, output_basename, chunk_size in [(databases['charadb'], "chara", "charadb", 500), (databases['musicdb'], "music", "musicdb", 500)]:
        chunks = [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

        for idx, chunk in enumerate(chunks):
            xml = E.database(
                *[E(elm_name, *popndll.serialize_data(x), id=str(x['_id'])) for x in chunk]
            )

            output_filename = os.path.join(output_base_folder, "%s_%d.xml" % (output_basename, idx))
            open(output_filename, "wb").write(tostring(xml, pretty_print=True, method='xml', encoding='cp932', xml_declaration=True).replace(b"cp932", b"shift-jis"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-dll', help='Input DLL file', default=None, required=True)
    parser.add_argument('--input-xml', help='Input XML file', default=None, required=True)
    parser.add_argument('--output', help='Output folder', default="output")

    args = parser.parse_args()
    databases = popndll.parse_database_from_dll(args.input_dll, args.input_xml)
    save_databases(databases, args.output)
#!/usr/bin/env python3
# Authors: Alessandro Lisi & Michael C. Campbell
# Be sure to install librsvg beforehand (brew install rsvg) or for Linux machine "https://manpages.ubuntu.com/manpages/trusty/man1/rsvg-convert.1.html"

# Use "python LAP.py --help" to see the options

import argparse
import xml.etree.ElementTree as ET
import os
import subprocess

def insert_colored_regions(svg_file, bed_file, output_file, individual_name, ancestries):

    chromosome_coordinates = {
        'chromosome1_hap1': {'x': 790.200, 'y': 333.200, 'width': 21, 'height': 435.500},
        'chromosome1_hap2': {'x': 811.100, 'y': 333.200, 'width': 21, 'height': 435.500},
        'chromosome2_hap1': {'x': 853.000, 'y': 104.10, 'width': 21, 'height': 664.200},
        'chromosome2_hap2': {'x': 873.900, 'y': 104.10, 'width': 21, 'height': 664.200},
        'chromosome3_hap1': {'x': 915.700, 'y': 194.600, 'width': 21, 'height': 573.700},
        'chromosome3_hap2': {'x': 936.700, 'y': 194.600, 'width': 21, 'height': 573.700},
    }

    # Chromosome Lengths
    chromosome_lengths = [
        310827022, 474425716, 409777670
    ]

    # Parsing the original SVG file
    original_svg_tree = ET.parse(svg_file)
    original_svg_root = original_svg_tree.getroot()

    # Add the individual's name as a title in the SVG file
    title_element = ET.Element('text', {'x': "800", 'y': "30", 'fill': "black", 'font-size': "32"})
    title_element.text = individual_name
    original_svg_root.insert(0, title_element)  # Insert the title at the beginning of the document

    rectangle_elements = []
    line_elements = []
    found_ancestries = set()

    # Extract regions from the BED file and add them to the SVG
    with open(bed_file, 'r') as bed:
        for line in bed:
            line = line.strip()
            if line.startswith("#"):
                continue

            parts = line.split('\t')
            if len(parts) < 6:
                continue

            chromosome, start, end, line_type, color, haplotype = parts[:6]
            chromosome = int(chromosome)
            start, end, haplotype = int(start), int(end), int(haplotype)

            chromosome_id = f'chromosome{chromosome}_hap{haplotype}'
            if chromosome_id in chromosome_coordinates:
                chromosome_data = chromosome_coordinates[chromosome_id]
                chromosome_length = chromosome_lengths[chromosome - 1]

                x = chromosome_data['x']
                width = chromosome_data['width']
                start_y = chromosome_data['y'] + (start / chromosome_length) * chromosome_data['height']
                end_y = chromosome_data['y'] + (end / chromosome_length) * chromosome_data['height']

                if line_type == 'geom_line':
                    offset = 15
                    line_element_start = ET.Element('line', {
                        'x1': str(x - offset),
                        'y1': str(start_y),
                        'x2': str(x + width + offset),
                        'y2': str(start_y),
                        'stroke': color,
                        'stroke-width': '2',
                        'stroke-dasharray': '10'
                    })
                    line_element_end = ET.Element('line', {
                        'x1': str(x - offset),
                        'y1': str(end_y),
                        'x2': str(x + width + offset),
                        'y2': str(end_y),
                        'stroke': color,
                        'stroke-width': '2',
                        'stroke-dasharray': '10'
                    })
                    original_svg_root.insert(0, line_element_start)
                    original_svg_root.insert(0, line_element_end)
                else:
                    rect_element = ET.Element('rect', {
                        'x': str(x),
                        'y': str(start_y),
                        'width': str(width),
                        'height': str(end_y - start_y),
                        'fill': color
                    })
                    rectangle_elements.append(rect_element)

                # Aggiungi l'ancestry trovata
                for ancestry_name, ancestry_color in ancestries.items():
                    if color == ancestry_color:
                        found_ancestries.add((ancestry_name, ancestry_color))

    for elem in rectangle_elements + line_elements:
        original_svg_root.insert(0, elem)

    # Crea la legenda solo con le ancestries trovate
    if found_ancestries:
        y_offset = 40  # Start drawing the legend from this y coordinate
        for name, color in found_ancestries:
            rect_element = ET.Element('rect', {'x': "1450", 'y': str(y_offset), 'width': "25", 'height': "15", 'fill': color})
            original_svg_root.insert(0, rect_element)

            # Text for the ancestry
            text_element = ET.Element('text', {'x': "1480", 'y': str(y_offset + 12), 'fill': "black", 'font-size': "16"})
            text_element.text = name
            original_svg_root.insert(0, text_element)

            y_offset += 30  # Update the y coordinate for the next entry in the legend

    # Save the modified result in the SVG file
    original_svg_tree.write(output_file)

    # Call rsvg-convert to convert the SVG file to a different format (e.g., PDF)
    output_format = "pdf"
    input_svg = output_file
    output_file_pdf = os.path.splitext(output_file)[0] + f'.{output_format}'
    subprocess.run(["rsvg-convert", "-f", output_format, "-o", output_file_pdf, input_svg])
    print(f"File converted to {output_format}: {output_file_pdf}")
    
def parse_svg_filename(filename):
    if not filename.endswith('.svg'):
        filename += '.svg'
    return filename

def main():
    parser = argparse.ArgumentParser(description='Insert colored regions from a BED file into an SVG file.')
    parser.add_argument('-B', type=parse_svg_filename, default='hg38', help='Input build38 "hg38" file without extension')
    parser.add_argument('-I', type=str, required=True, help='Input BED file')
    parser.add_argument('-O', type=str, required=True, help='Output SVG file')

    args = parser.parse_args()

    # Default colors for ancstries
    default_ancestry_colors = [
        ("ancestry0", "#a32e2e"),
        ("ancestry1", "#26962b"),
        ("ancestry2", "#bfa004"),
        ("ancestry3", "#d18311"),
        ("ancestry4", "#22ba9d"),
        ("ancestry5", "#839dfc"),
        ("ancestry6", "#9a5dc1"),
        ("ancestry7", "#0a0ae0"),
        ("ancestry8", "#707070"),
        ("ancestry9", "#00cfff"),
        ("ancestry10", "#790ee0"),
    ]

  
    with open(args.I, 'r') as bed_file:
        header_line = bed_file.readline().strip()
        if header_line.startswith("#Subpopulation order/codes:"):
            ancestry_names = header_line.split(":")[1].strip().split()
            ancestry_map = {}
            for item in ancestry_names:
                name, code = item.split("=")
                ancestry_map[int(code)] = name

            ancestries = {ancestry_map.get(i, f'ancestry{i}'): color for i, (name, color) in enumerate(default_ancestry_colors)}
        else:
            ancestries = {name: color for name, color in default_ancestry_colors}

    individual_name = os.path.basename(args.I).split('.')[0]

    insert_colored_regions(args.B, args.I, args.O, individual_name, ancestries)

if __name__ == "__main__":
    main()

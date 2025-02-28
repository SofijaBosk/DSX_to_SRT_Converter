import sys
import xml.etree.ElementTree as ET
import os
from logging import ERROR
import tkinter as tk
from tkinter import messagebox
import re

def format_text_with_italics_and_breaks(element):
    """Recursively extract text from an element, wrapping italic text and handling line breaks."""
    text_parts = []

    if element.text:
        text_parts.append(element.text.strip())
    for child in element:
        if 'br' in child.tag:  # Handle <tt:br/>
            text_parts.append('\n')  # Insert a new line for <tt:br/>
        if child.tag.endswith('span') and child.attrib.get('{http://www.w3.org/ns/ttml#styling}fontStyle') == 'italic':
            # Wrap the italic text and process its children recursively
            for ch in child:
                if 'br' in ch.tag:  # Handle <tt:br/>
                    text_parts.append('\n')
            text_parts.append(f"<i>{format_text_with_italics_and_breaks(child)}</i>")
        else:
            # Process other child elements
            text_parts.append(format_text_with_italics_and_breaks(child))

        # Handle tail text after the child element
        if child.tail:
            text_parts.append(child.tail.strip())

    return ''.join(text_parts).strip()

def convert_frame_to_milliseconds(frames, frame_rate):
    """Convert time from HH:MM:SS,FF format to HH:MM:SS,ms"""
    if frames == 0:
        return 0
    return int(round(float(frames)*frame_rate,2)*100)


def extract_frame_rate(root):
    """Extracting frame rate from the UXML document."""
    frame_rate_element = root.find('.//{http://www.sdimedia.com/ns/uxml/5.10/uxml}frameRate')
    if frame_rate_element is not None:
        return float(frame_rate_element.text.replace(',','.'))/60
    else:
        print("ERROR: No framerate found")  # Default frame rate if not found

def convert_uxml_to_srt(uxml_file, srt_file):
    try:
        # Parsing the input UXML file
        tree = ET.parse(uxml_file)
        root = tree.getroot()

        namespaces = {
            'tt': 'http://www.w3.org/ns/ttml',
            'sdi': 'http://www.sdimedia.com/ns/uxml/5.10/ttml-ext'
        }

        # Extracting frame rate from the UXML
        frame_rate = extract_frame_rate(root)

        with open(srt_file, 'w', encoding='utf-8') as f:
            counter = 1

            for p in root.findall('.//tt:p', namespaces):
                start_time = p.get('begin')
                end_time = p.get('end')

                text = format_text_with_italics_and_breaks(p)
                if not text:  # Skip empty subtitles
                    continue


                # Format times for SRT
                start_time = start_time.replace('.', ',') if start_time else "00:00:00,000"
                end_time = end_time.replace('.', ',') if end_time else "00:00:00,000"

                start_time, start_frames = start_time.split(',')
                end_time, end_frames = end_time.split(',')

                # Convert times for SRT
                start_time_frames = convert_frame_to_milliseconds(start_frames, frame_rate)
                end_time_frames = convert_frame_to_milliseconds(end_frames, frame_rate)

                # Format time for SRT as HH:MM:SS,ms
                start_time_formatted = f"{start_time},{start_time_frames:03}"
                end_time_formatted = f"{end_time},{end_time_frames:03}"

                start_time_formatted = convert_time_format(start_time_formatted)
                end_time_formatted = convert_time_format(end_time_formatted)
                # Format text for SRT with newlines
                # formatted_text = format_srt_text(text)

                # Write subtitle
                f.write(f"{counter}\n")
                f.write(f"{start_time_formatted} --> {end_time_formatted}\n")
                f.write(f"{text}\n\n")
                counter += 1

        print(f"Conversion successful! Saved to {srt_file}.")

    except Exception as e:
        print(f"An error occurred while processing {uxml_file}: {e}")


def convert_all_dsx_in_folder(input_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith('.dsx'):
            uxml_file_path = os.path.join(input_folder, filename)
            srt_file_path = os.path.join(output_folder, f"{os.path.splitext(filename)[0]}.srt")
            convert_uxml_to_srt(uxml_file_path, srt_file_path)

def convert_time_format(time_str):
    # Parse the input time string using regex
    match = re.match(r"(\d{2}):(\d{2}):(\d{2}),(\d{3,6})", time_str)
    if not match:
        raise ValueError("Invalid time format. Expected HH:MM:SS,MMM")


    # Extract hours, minutes, seconds, and milliseconds
    hours, minutes, seconds, milliseconds = map(int, match.groups())
    total_ms = (hours * 3600 * 1000) + (minutes * 60 * 1000) + (seconds * 1000) + milliseconds

    # if milliseconds>=1000:
    #     print("PRE:")
    #     print(f"Org: {time_str}")
    #     print(f"Milisec{milliseconds}")
    #     print(total_ms)
    # Convert the entire time to milliseconds

    # Convert back to hours, minutes, seconds, and milliseconds
    new_hours = total_ms // (3600 * 1000)
    total_ms %= (3600 * 1000)

    new_minutes = total_ms // (60 * 1000)
    total_ms %= (60 * 1000)

    new_seconds = total_ms // 1000
    new_milliseconds = total_ms % 1000
    # print(f"{new_hours:02}:{new_minutes:02}:{new_seconds:02},{new_milliseconds:03}")
    # Format the result back to HH:MM:SS,MMM
    # if milliseconds>=1000:
    #     print("POSLE:")
    #     print(f"{new_hours:02}:{new_minutes:02}:{new_seconds:02},{new_milliseconds:03}")
    #     print(f"Milisec{new_milliseconds}")
    #     print(total_ms)
    return f"{new_hours:02}:{new_minutes:02}:{new_seconds:02},{new_milliseconds:03}"

def show_popup():
    # Create a new Tkinter window (this won't be shown)
    root = tk.Tk()
    root.withdraw()  # Hide the root window
    messagebox.showinfo("Process Information", "The files have been converted to srt")  # Show the popup
    root.destroy()  # Destroy the root window after the message is closed


def main():

    input_folder = 'dsx input files'  # Replace with your input folder path
    output_folder = 'srt output files'  # Desired output folder path

    # Construct the full path
    input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), input_folder)
    output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), output_folder)
    convert_all_dsx_in_folder(input_folder, output_folder)

    show_popup()

if __name__ == "__main__":
    main()



import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
import threading
import sys
import time
import itertools
import os


def display_banner():
    print(r"""
__     ___   _  ____                     _
\ \   / / \ | |/ ___|_ __ ___  ___  ___ | |_   _____ _ __
 \ \ / /|  \| | |   | '__/ _ \/ __|/ _ \| \ \ / / _ \ '__|
  \ V / | |\  | |___| | |  __/\__ \ (_) | |\ V /  __/ |
   \_/  |_| \_|\____|_|  \___||___/\___/|_| \_/ \___|_|
       Data Fetcher client
                by Kim Schulz <kim@schulz.dk>
                """)


def fetch_data(country_code):
    url = f"https://computernewb.com/vncresolver-next/api/v1/search?country={country_code}&full=true"
    response = requests.get(url)
    data = response.json()
    for obj in data["results"]:
        id = str(obj["id"])
        obj["imagelink"] = (
            f"https://computernewb.com/vncresolver-next/api/v1/screenshot/{id}"
        )
    return data


def show_spinner(stop_event):
    spinner = itertools.cycle(["-", "/", "|", "\\"])
    while not stop_event.is_set():
        sys.stdout.write(next(spinner))  # write the next character
        sys.stdout.flush()  # flush stdout buffer (actual character display)
        time.sleep(0.1)
        sys.stdout.write("\b")  # erase the last written char


def save_as_html(data, filename, download_images):
    if download_images:
        os.makedirs("images", exist_ok=True)
    with open(filename, "w") as f:
        f.write("""
        <html>
        <head>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f9;
                }
                .container {
                    width: 80%;
                    margin: 20px auto;
                    background-color: #fff;
                    padding: 20px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }
                .item {
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                    border-bottom: 1px solid #ddd;
                    padding-bottom: 10px;
                }
                .item img {
                    min-width: 650px;
                    max-width: 650px;
                    margin-right: 20px;
                }
                .item table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .item table, .item th, .item td {
                    border: 1px solid #ddd;
                }
                .item th, .item td {
                    padding: 8px;
                    text-align: left;
                }
                .item th {
                    background-color: #f2f2f2;
                }
            </style>
        </head>
        <body>
            <div class="container">
        """)
        if download_images:
            print("\bFetching images:")
        for obj in data["results"]:
            if download_images:
                print(f"  - fetching {obj['id']}....", end="")
                image_filename = f"images/{obj['id']}.png"
                image_data = requests.get(obj["imagelink"]).content
                with open(image_filename, "wb") as img_file:
                    img_file.write(image_data)
                image_src = image_filename
                print("\bdone")
            else:
                image_src = obj["imagelink"]

            f.write(f"<div class='item'><img src='{image_src}' alt='Image'><table>")
            f.write("<tr><th>Key</th><th>Value</th></tr>")
            for key, value in obj.items():
                if key != "imagelink":
                    f.write(f"<tr><td>{key}</td><td>{value}</td></tr>")
            f.write("</table></div>")
        if not download_images:
            f.write("""
            <script>
                document.querySelectorAll('img').forEach(img => {
                    const src = img.getAttribute('src');
                    fetch(src)
                        .then(response => response.blob())
                        .then(blob => {
                            const url = URL.createObjectURL(blob);
                            img.src = url;
                        });
                });
            </script>
            """)
        f.write("""
            </div>
        </body>
        </html>
        """)


def save_as_json(data, filename):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)


def save_as_xml(data, filename):
    root = ET.Element("results")
    for obj in data["results"]:
        item = ET.SubElement(root, "item")
        for key, value in obj.items():
            child = ET.SubElement(item, key)
            child.text = str(value)
    tree = ET.ElementTree(root)
    tree.write(filename)


def main():
    display_banner()
    country_code = input("Enter the 2-letter ISO country code: ").upper()
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event,))
    spinner_thread.start()
    print("Fetching data....", end="")

    start_time = time.time()
    data = fetch_data(country_code)
    stop_event.set()
    spinner_thread.join()
    print("\bdone")
    print(f"\nFetched {len(data['results'])} objects.")

    print("How would you like the output to be formatted?")
    print("1. HTML file")
    print("2. JSON file")
    print("3. XML file")
    choice = input("Enter your choice (1/2/3): ")

    date_str = datetime.now().strftime("%d-%m-%Y-%H.%M.%S")
    filename = f"{country_code}-{date_str}"
    stop_event = threading.Event()
    spinner_thread = threading.Thread(target=show_spinner, args=(stop_event,))

    if choice == "1":
        download_images = input(
            "Do you want to download the image files? (Yes/No): "
        ).strip().lower() in ["yes", "y"]
        print("Saving as html")
        spinner_thread.start()
        save_as_html(data, f"{filename}.html", download_images)
    elif choice == "2":
        print("Saving as json")
        spinner_thread.start()
        save_as_json(data, f"{filename}.json")

    elif choice == "3":
        print("Saving as xml")
        spinner_thread.start()
        save_as_xml(data, f"{filename}.xml")
    else:
        print("Invalid choice.")
        return
    stop_event.set()
    spinner_thread.join()

    end_time = time.time()
    print(
        f"Completed. Output file: {filename}. Time taken: {end_time - start_time:.2f} seconds."
    )


if __name__ == "__main__":
    main()

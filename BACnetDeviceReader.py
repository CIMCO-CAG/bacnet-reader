import os, sys
import csv
import BAC0
#may need to install this as well: pyasynchat, pytz
import psutil
import tkinter
import threading
import socket
import logging
import ToolTip as tt
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from ttkthemes import ThemedTk
from tkinter import messagebox
from PIL import Image, ImageTk

class BacnetObject:
    def __init__(self, mac, objectType, objectValue, deviceID):
        self.mac = mac
        self.objectType = objectType
        self.objectValue = objectValue
        self.deviceID = deviceID
        self._presentValue = None
        self._objectName = None
        self._objectIdentifier = None
        self._status = None
        self._description = None
        self.deviceid = None

    @property
    def presentValue(self):
        if self._presentValue is None:
            try:
                self._presentValue = bacnet.read(f'{self.mac} {self.objectType} {self.objectValue} presentValue')
            except:
                self._status = ""
        return self._presentValue

    @property
    def objectName(self):
        if self._objectName is None:
            self._objectName = bacnet.read(f'{self.mac} {self.objectType} {self.objectValue} objectName')
        return self._objectName

    @property
    def objectIdentifier(self):
        if self._objectIdentifier is None:
            raw_identifier = bacnet.read(f'{self.mac} {self.objectType} {self.objectValue} objectIdentifier')
            self._objectIdentifier = self._format_identifier(raw_identifier)
        return self._objectIdentifier

    @property
    def status(self):
        if self._status is None:
            try:
                self._status = bacnet.read(f'{self.mac} {self.objectType} {self.objectValue} statusFlags')
                # Define the status labels
                status_labels = ["In Alarm", "Fault", "Overridden", "Out of Service"]

                # Create a dictionary to map indices to status labels
                status_dict = {i: label for i, label in enumerate(status_labels)}

                # Convert the input list to a string representation of status
                self._status = ", ".join(status_dict[i] for i in range(len(self._status)) if self._status[i] == 1)

            except:
                self._status = ""
        return self._status

    @property
    def description(self):
        if self._description is None:
            try:
                if 150 == self.objectType or  141 == self.objectType or  147 == self.objectType:
                    self._description = ""
                else:
                    self._description = bacnet.read(f'{self.mac} {self.objectType} {self.objectValue} description')
            except:
                self._description = ""
        return self._description

    def _format_identifier(self, raw_identifier):
        if len(raw_identifier) != 2:
            return 'Unknown'
        type, number = raw_identifier
        type_to_abbr = {
            'analogValue': 'AV', 'analogInput': 'AI', 'analogOutput': 'AO',
            'binaryValue': 'BV', 'binaryInput': 'BI', 'binaryOutput': 'BO',
            'multiStateValue': 'MSV'
        }
        type_abbr = type_to_abbr.get(type, type)
        return f'{type_abbr}{number}'

# GUI
window_width = 950
window_height = 750
root = ThemedTk(theme="arc")
root.title("BACnet Device Reader - v2024.07.30")
root.geometry(f"{window_width}x{window_height}")
root.configure(bg='light grey')  # Set the background color
text_font = ("Open Sans", 10)
title_font = ("Open Sans", 10,"bold")
seperator_font = ("Open Sans", 12,"bold")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
center_x = int((screen_width - window_width) / 3)
center_y = int((screen_height - window_height) / 2)
root.geometry(f"+{center_x}+{center_y}")

addrs = psutil.net_if_addrs()
options_dict = {}
WiFi = []
Ethernet = []

for adapter, addresses in addrs.items():
    if 'Wi-Fi' in adapter:
        for addr in addresses:
            if addr.family == socket.AF_INET:
                options_dict[f'Wi-Fi : {addr.address}'] = addr.address
                WiFi.append(f"{addr.address}")

# Find Ethernet adapters and append to options_dict
ethernet_count = else_count = 1
eth_found = False
for adapter, addresses in addrs.items():
    if 'Ethernet' in adapter:
        eth_found = True
        for addr in addresses:
            if addr.family == socket.AF_INET:
                options_dict[f'Ethernet {ethernet_count} : {addr.address}'] = addr.address
                Ethernet.append(f"{addr.address}")
                ethernet_count += 1
if not eth_found:
    for adapter, addresses in addrs.items():
        for addr in addresses:
                if addr.family == socket.AF_INET:
                    options_dict[f'IP {else_count} : {addr.address}'] = addr.address
                    Ethernet.append(f"{addr.address}")
                    else_count += 1
    messagebox.showwarning(title="Warning", message="No adapter with 'Ethernet' in name was found. Displaying all IPs.")


def save_folder_location(folder_location):
    with open("folder_location.txt", "w") as file:
        file.write(folder_location)

def load_folder_location():
    if os.path.exists("folder_location.txt"):
        with open("folder_location.txt", "r") as file:
            return file.read().strip()  # Remove leading/trailing whitespace
    else:
        return None

print("Wi-Fi IPv4 Address: ", WiFi)
print("Ethernet IPv4 Address: ", Ethernet)

Address = Ethernet[0]

# Load the folder location from the file
loaded_folder_location = load_folder_location()

# Set default_folder to loaded_folder_location or os.getcwd() if empty
default_folder = loaded_folder_location or os.getcwd()

tags_file_path = f'{os.curdir}/tags.txt'
translate_file_path = f'{os.curdir}/translate.ini'
port = 47808
all_objects = {}
objects_for_device = {}
extra_objects_for_device = {}
combined_objects = []
current_list = []
saved_objects = []
devices = []

# Frame for device selection
frame1 = ttk.LabelFrame(root, text="", padding="10")
frame1.grid(row=0, column=0, padx=(15, 5), pady=(15, 5), sticky=(tk.W, tk.E, tk.N, tk.S))
frame1.configure(relief='groove', borderwidth=2)

# Frame for object selection
frame2 = ttk.LabelFrame(root, padding="10")
frame2.grid(row=1, column=0, padx=(15,5), pady=(5,15),sticky=(tk.W, tk.E, tk.N, tk.S))
frame2.configure(relief='groove', borderwidth=2)

# Frame for displaying objects
frame3 = ttk.LabelFrame(root, padding="10",)
frame3.grid(row=0, column=1,padx=(10,15),pady=(15),rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
frame3.configure(relief='groove', borderwidth=2)

frame3.grid_columnconfigure(0, weight=1)
frame3.grid_rowconfigure(0, weight=1)
frame3.grid_rowconfigure(1, weight=2)
frame3.grid_rowconfigure(2, weight=8)
frame3.grid_rowconfigure(3, weight=2)
frame3.grid_rowconfigure(4, weight=8)
frame3.grid_rowconfigure(5, weight=1)
frame3.grid_rowconfigure(6, weight=1)
frame3.grid_rowconfigure(7, weight=1)
frame3.grid_rowconfigure(8, weight=1)

root.grid_columnconfigure(1, weight=1)
root.grid_rowconfigure(0, weight=1)
root.grid_rowconfigure(1, weight=1)

# Label for Device Selection
object_type_label = ttk.Label(frame2, text="Object Type Selection:\n",font = title_font)
object_type_label.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

# Label for Device Selection
device_label = ttk.Label(frame1, text="Devices:\n",font = title_font)
device_label.grid(row=8, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

device_var = tk.StringVar(root)
device_var.set('Select Device')  # Set default value
device_menu = ttk.Combobox(frame1, textvariable=device_var, values=devices, width=25,font=text_font)
device_menu.grid(row=9, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

space1_label = ttk.Label(frame1, text="----------------------------------------",font=seperator_font)
space1_label.grid(row=3, column=0, pady=(5, 0), sticky=(tk.W, tk.E))

# Label for port entry
port_label = ttk.Label(frame1, text="Port Number:\n",font=title_font)
port_label.grid(row=4, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

loading_label = ttk.Label(frame1, text="")
loading_label.update()
loading_label.grid(row=10, column=0, pady=(5, 0), sticky=(tk.W, tk.E))

# Entry for port number
port_var = tk.StringVar(root)
port_var.set("47808")  # Setting the default value to 47808
port_entry = ttk.Entry(frame1, textvariable=port_var)
port_entry.config(width=5)  # Explicitly setting the width of the Entry widget
port_entry.grid(row=5, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

space2_label = ttk.Label(frame1, text="----------------------------------------",font=seperator_font)
space2_label.grid(row=7, column=0, pady=(5, 0), sticky=(tk.W, tk.E))

# Label for port entry
Address_label = ttk.Label(frame1, text="Network Card / IP Address:\n",font = title_font)
Address_label.grid(row=0, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

# Entry for port number
Address_var = tk.StringVar(root)
Address_var.set("")
# Define the options for the combobox
options = list(options_dict.keys())  # Use the keys from the dictionary
# Create a combobox with the options
Address_entry = ttk.Combobox(frame1, textvariable=Address_var, values=options)
# Set the default value to the first option
Address_entry.set(options[1])
# Configure the width of the combobox
Address_entry.config(width=5)
# Place the combobox on the grid
Address_entry.grid(row=1, column=0, padx=(0, 10), sticky=(tk.W, tk.E))

# List of object types
object_types = ['analogValue', 'binaryValue',  'analogInput', 'binaryInput', 'analogOutput', 'binaryOutput','multiStateValue','multiStateInput','multiStateOutput']
selected_types = tk.StringVar(value=object_types)
type_listbox = tk.Listbox(frame2, listvariable=selected_types, selectmode='extended', height = 9,font=text_font, exportselection=False)
default_selection = [i for i in range(len(object_types)) if object_types[i] not in ('multiStateValue', 'multiStateInput', 'multiStateOutput')]
type_listbox.grid(row=1, column=0, padx=(0, 23), sticky=(tk.W, tk.E))

# Label for port entry
object_label = ttk.Label(frame3, text="Object Display:",font = title_font)
object_label.grid(row=0, column=0, padx=(0, 10), sticky=('WENS'))

# List of displaying objects
object_names = []  # Initialize with an empty list
selected_types2 = tk.StringVar(value=object_names)
object_frame = tk.Frame(frame3)
object_frame.grid(row=2, column=0, sticky=('WENS'))
object_listbox = tk.Listbox(object_frame, listvariable=selected_types2, selectmode='extended',font=text_font, exportselection=False)

# Create a frame to contain the listbox and scrollbar
object_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

def show_loading_popup():
    global loading_popup
    loading_popup = tk.LabelFrame(object_frame, background="white", text="Loading Objects...")
    loading_popup.place(relx=0, rely=0, relwidth=1, relheight=1)
    loading_popup.update_idletasks()

def hide_loading_popup():
    if loading_popup:
        loading_popup.place_forget()

# Create the scrollbar inside the new frame
ObjectScrollbar = tk.Scrollbar(object_frame)
ObjectScrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Link the scrollbar to the listbox
object_listbox.config(yscrollcommand=ObjectScrollbar.set)
ObjectScrollbar.config(command=object_listbox.yview)

# Label for port entry
comparison_label = ttk.Label(frame3, text="Contents of Tags.txt:",font = title_font)
comparison_label.grid(row=3, column=0, padx=(0, 10), sticky=('WENS'))

# List of displaying comparison objects
comparison_frame = tk.Frame(frame3)
comparison_frame.grid(row=4, column=0, sticky=('WENS'))
comparison_listbox = tk.Listbox(comparison_frame, selectmode='extended',font=text_font, exportselection=False)

# Create a frame to contain the listbox and scrollbar
comparison_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

# Create the scrollbar inside the new frame
ComparisonScrollbar = tk.Scrollbar(comparison_frame)
ComparisonScrollbar.pack(side=tk.RIGHT, fill=tk.Y)

# Link the scrollbar to the listbox
comparison_listbox.config(yscrollcommand=ComparisonScrollbar.set)
ComparisonScrollbar.config(command=comparison_listbox.yview)

type_listbox.select_set(0,5)

def read_objects_chunk(mac, device_id, object_chunk):
    global allowed_types
    allowed_types = {
        'analogValue', 'binaryValue', 'analogInput', 'binaryInput', 'analogOutput', 'binaryOutput', 'multiStateValue', 'multiStateInput', 'multiStateOutput'
    }
    bacnet_objects = [
        BacnetObject(mac, obj[0], obj[1], device_id)
        for obj in object_chunk if obj[0] in allowed_types
    ]
    if mac not in objects_for_device:
        objects_for_device[mac] = []
    objects_for_device[mac].extend(bacnet_objects)
    combined_objects.extend(bacnet_objects)

    for obj in bacnet_objects:
        print(f"Loaded object: {obj.deviceID}.{obj.objectIdentifier} - {obj.objectName}")

def read_objects_for_device(mac, device_id):
    try:
        object_list = bacnet.read(f'{mac} device {device_id} objectList')
        chunk_size = 10  # Define the chunk size
        threads = []

        for i in range(0, len(object_list), chunk_size):
            chunk = object_list[i:i + chunk_size]
            # Create a thread for each chunk
            thread = threading.Thread(target=read_objects_chunk, args=(mac, device_id, chunk))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    except Exception as e:
        loading_label.config(text="")
        loading_label.update()
        print(f"Error reading objects for device {device_id}: {e}")

def Network_Connect():
    def connect_and_discover():
        loading_label.config(text="Loading Devices...")
        loading_label.update()
        try:
            type_listbox.select_set(0, 5)
            try:
                global bacnet
                global all_devices
                success = False
                try:
                    bacnet = BAC0.connect(ip=Address, port=port)
                    success = True
                except Exception as e:
                    success = False
                    loading_label.config(text="")
                    loading_label.update()
                    print(f"Error connecting to BACnet network: {e}")
                    messagebox.showerror(title="Error", message=
"Could not connect to BACnet network. Please check that \
no other BACnet application is using this IP address and port.")

                if success:
                    bacnet.discover()
                    all_devices = bacnet.devices

                    if all_devices:
                        print("Found BACnet devices:")
                        loading_label.config(text="BACnet devices found.")
                        loading_label.update()
                        for idx, (a, b, mac, device_id) in enumerate(all_devices):
                            print(f"Device {device_id} ({mac})")
                    else:
                        loading_label.config(text="")
                        loading_label.update()
                        messagebox.showerror(title="Error", message="No BACnet devices found on this port and network.")
                devices = ['Show All Devices'] + [f'{device[0]} ({device[3]})' for device in bacnet.devices]
                device_menu['values'] = devices
                loading_label.config(text="")
                loading_label.update()
            except Exception as e:
                print(f"An error occurred: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
            pass

    threading.Thread(target=connect_and_discover).start()

# Function to change port number
def change_port():
    type_listbox.select_set(0,5)
    global port
    try:
        port = int(port_var.get())
        # Connect to the BACnet network
        bacnet.disconnect()
        Network_Connect()
    except:
        pass

# Function to change port number
def change_Address():
    type_listbox.select_set(0,5)
    global Address
    try:
        key = str(Address_var.get())
        Address = options_dict[key]  # Get the value from the dictionary
        # Connect to the BACnet network
        bacnet.disconnect()
        Network_Connect()
    except:
        print("Exception in address change")
        pass

# Button to change port number
change_port_button = ttk.Button(frame1, text="Change Port", command=change_port)
change_port_button.grid(row=6, column=0, pady=(10, 0),padx=(0, 10), sticky=('WENS'))
change_port_button_ttp = tt.CreateToolTip(change_port_button, \
    "Changes port number to input.")

# Button to change Address
change_Address_button = ttk.Button(frame1, text="Change Address", command=change_Address)
change_Address_button.grid(row=2, column=0, pady=(10, 0),padx=(0, 10), sticky=('WENS'))
change_port_button_ttp = tt.CreateToolTip(change_Address_button, \
    "Changes address to Ethernet or Wi-Fi")

def connect_device():
    type_listbox.select_set(0,5)
    try:
        new_port = int(port_var.get())
        # Here you can add the code to change the port number
        print("Success", f"Port number changed to {new_port}")
    except ValueError:
        tkinter.messagebox.showerror(title="Error", message="No BACnet devices found on this port and network.")

def read_items_from_file(file_path):
    with open(file_path, 'r') as file:
        items = [line.strip() for line in file]
    return items

def write_items_to_file(file_path, items):
    with open(file_path, 'w') as file:
        for item in items:
            file.write(item + '\r' + '\n')

# Function to delete selected items from the listbox and update the file
def delete_selected_items():
    selected_indices = comparison_listbox.curselection()
    if selected_indices:
        items = read_items_from_file(tags_file_path)
        for index in reversed(selected_indices):
            del items[index]
        write_items_to_file(tags_file_path, items)

        items = read_items_from_file(translate_file_path)
        for index in reversed(selected_indices):
            del items[index+1]
        write_items_to_file(translate_file_path, items)

        update_comparison_listbox()

def update_comparison_listbox():
    comparison_listbox.delete(0, tk.END)
    items = read_items_from_file(tags_file_path)
    for item in items:
        comparison_listbox.insert(tk.END, item)

def update_object_listbox(event):
    selected = type_listbox.curselection()

    if selected:
        selected_types = [type_listbox.get(i) for i in selected]
        filtered_objects = [f"{obj.deviceID}.{obj.objectIdentifier} - {obj.objectName}" for obj in current_list if obj.objectType in selected_types]
    else:
        filtered_objects = [f"{obj.deviceID}.{obj.objectIdentifier} - {obj.objectName}" for obj in current_list]

    displayed_items = object_listbox.get(0, tk.END)

    for item in displayed_items:
        if item not in filtered_objects:
            index = object_listbox.get(0, tk.END).index(item)
            object_listbox.delete(index)

    for item in filtered_objects:
        if item not in displayed_items:
            object_listbox.insert(tk.END, item)

    object_listbox.select_set(0, tk.END)

def update_device(event):
    def load_objects():
        loading_label.config(text="Loading Objects...")
        loading_label.update()
        show_loading_popup()
        type_listbox.select_set(0, 5)
        selected_device = device_var.get()
        global current_list

        if selected_device == 'Show All Devices':
            current_list = combined_objects
            update_object_listbox(object_listbox)
            loading_label.config(text="")
            loading_label.update()
            hide_loading_popup()
        else:
            for device_info in all_devices:
                device_name = f'{device_info[0]} ({device_info[3]})'
                if selected_device == device_name:
                    mac = device_info[2]
                    if mac in objects_for_device:
                        current_list = objects_for_device[mac]
                        update_object_listbox(object_listbox)
                        loading_label.config(text="")
                        loading_label.update()
                        hide_loading_popup()
                    else:
                        read_objects_for_device(mac, device_info[3])
                        current_list = objects_for_device[mac]
                        update_object_listbox(object_listbox)
                        loading_label.config(text="")
                        loading_label.update()
                        hide_loading_popup()
                    break

    threading.Thread(target=load_objects).start()

# Bind the update_device function to the Combobox selection event
device_menu.bind("<<ComboboxSelected>>", update_device)
type_listbox.bind("<<ListboxSelect>>", update_object_listbox)

# Initialize the default folder to the current directory
try:
    folder_parts = default_folder.split(os.path.sep)
    shortened_folder = os.path.sep.join(folder_parts[-2:])
    shortened_folder = str(shortened_folder)
    if len(shortened_folder) > 50:
        shortened_folder = "..." + shortened_folder[-47:]
        shortened_folder = shortened_folder.split('/', 1)[-1]
    selected_folder_label = ttk.Label(frame3, text=f"Selected Folder: {os.path.sep}{shortened_folder}", justify='center', font=('Courier', 10), foreground='black')
    selected_folder_label.grid(row=8, column=0, sticky=('WENS'))
except:
    print('Failed to construct a folder path')
    pass

def select_folder():
    global default_folder  # Declare the variable as global at the beginning of the function
    global tags_file_path
    global translate_file_path
    global shortened_folder
    # Use a Tkinter dialog to select a folder
    folder = filedialog.askdirectory(initialdir=default_folder)

    # If a folder was selected, update the default folder
    if folder:
        save_folder_location(folder)
        default_folder = folder
        tags_file_path = f'{default_folder}/tags.txt'
        translate_file_path = f'{default_folder}/translate.ini'
        tkinter.messagebox.showinfo(title='Info',message=f"You have selected folder: {default_folder}")

        # Split the path using '/' as delimiter
        try:
            folders = default_folder.split('/')
        except:
            print("Failed to update folder")
            pass

        # Get the second last folder and last folder
        second_last_folder = folders[-2]
        last_folder = folders[-1]

        selected_folder_label.configure(text=f"Selected Folder: .../{second_last_folder}/{last_folder}")
        selected_folder_label.update_idletasks()

    # Print the selected folder for debugging
    print(f"Selected folder: {default_folder}")

def append_to_file():
    global default_folder

    selected = object_listbox.curselection()
    selected_objects = [object_listbox.get(i) for i in selected]

    # Map the selected strings back to BacnetObject instances
    selected_objects = [obj for obj in current_list if f"{obj.deviceID}.{obj.objectIdentifier} - {obj.objectName}" in selected_objects]

    # Check if the files exist
    translate_file = os.path.join(default_folder, 'translate.ini')
    tags_file = os.path.join(default_folder, 'tags.txt')
    if not os.path.exists(translate_file) or not os.path.exists(tags_file):
        tkinter.messagebox.showerror(title='Error', message='File(s) not found.')
        return

    # Append to translate.ini
    with open(translate_file, 'ab') as file:
        for obj in selected_objects:
            line = f'{obj.deviceID}.{obj.objectIdentifier}={obj.objectName}\r\n'
            file.write(line.encode())

    # Append to tags.txt
    with open(tags_file, 'ab') as file:
        for obj in selected_objects:
            if obj.objectType == 'binaryValue':
                symbol = 'BOOL'
            else:
                symbol = '%'
            line = f'{obj.deviceID}.{obj.objectIdentifier},{symbol},{obj.objectName}\r\n'
            file.write(line.encode())

    tkinter.messagebox.showinfo(title='Info', message='Data has been appended to the files.')
    update_comparison_listbox()

def save_to_files():
    global default_folder  # Declare the variable as global at the beginning of the function
    print("save_to_files called")  # Debugging print statement

    if os.path.isfile(tags_file_path) or os.path.isfile(translate_file_path):
        # Display the confirmation message
        result = messagebox.askquestion("Confirmation", "Tags.txt and/or translate.ini files already exist. Do you want to overwrite these?", icon='warning')
        # Handle the user's response (e.g., perform actions based on their choice)
        if result == "yes":
            # User chose to overwrite the files
            threading.Thread(target=save_to_files_thread, daemon=True).start()
        else:
            # User chose not to overwrite the files
            print("File saving cancelled.")
    else:
        # Neither file exists
        threading.Thread(target=save_to_files_thread, daemon=True).start()

def create_debug_window():
    global debug_window
    debug_window = tk.Toplevel()
    debug_window.title("Debug Information")

    # Change the protocol for closing debug window to withdrawing it,
    # instead of deleting the object
    debug_window.protocol("WM_DELETE_WINDOW", debug_window.withdraw)

    window_width = 800
    window_height = 400
    debug_window.geometry(f"{window_width}x{window_height}")

    # Position the window on the screen in top right corner
    screen_width = debug_window.winfo_screenwidth()
    screen_height = debug_window.winfo_screenheight()
    center_x = int((screen_width - window_width) * 7 / 8)
    center_y = int((screen_height - window_height) * 1 / 8)
    debug_window.geometry(f"+{center_x}+{center_y}")

    # Set a modern look with light grey background color
    debug_window.configure(bg='#f0f0f0')

    # Create a frame for the content with padding for a cleaner look
    content_frame = tk.Frame(debug_window, bg='#ffffff', padx=20, pady=20)
    content_frame.pack(fill='both', expand=True)

    # Add a label with a larger bold font for the title
    title_label = tk.Label(content_frame, text="Debug Information", bg='#f0f0f0', fg='black', font=("Helvetica", 16, "bold"))
    title_label.pack(pady=(0, 10))

    # console_text is a reference for stdout.write overrider to use
    global console_text
    console_text = tk.Text(content_frame, width = 100)
    console_text.pack()

# Unlike with information window, we created in the very beginning, and hide it then,
# and whenever user clicks to display it, we just show it, instead of recreating it.
def show_debug_window():
    debug_window.state('normal')

def show_information_window():
    # Create a new top-level window
    info_window = tk.Toplevel()
    info_window.title("Application Information")

    # Set the size of the window
    window_width = 600
    window_height = 500
    info_window.geometry(f"{window_width}x{window_height}")

    # Center the window on the screen
    screen_width = info_window.winfo_screenwidth()
    screen_height = info_window.winfo_screenheight()
    center_x = int((screen_width - window_width) / 2)
    center_y = int((screen_height - window_height) / 2)
    info_window.geometry(f"+{center_x}+{center_y}")

    # Set a modern look with light grey background color
    info_window.configure(bg='#f0f0f0')

    # Create a frame for the content with padding for a cleaner look
    content_frame = tk.Frame(info_window, bg='#f0f0f0', padx=20, pady=20)
    content_frame.pack(fill='both', expand=True)

    # Add a label with a larger bold font for the title
    title_label = tk.Label(content_frame, text="Application Information", bg='#f0f0f0', fg='black', font=("Helvetica", 16, "bold"))
    title_label.pack(pady=(0, 10))

    info_text = tk.Text(content_frame, wrap='word', bg='#ffffff', fg='black', bd=0, highlightthickness=0, font=("Helvetica", 10))
    info_text.tag_configure('bold', font=('Helvetica', 10, 'bold'))

    info_text.insert(tk.END, "Welcome to the BACnet Device Reader!\n\n", 'bold')
    info_text.insert(tk.END, "This application allows you to manage BACnet objects efficiently. Here are the key functionalities:\n\n")

    info_text.insert(tk.END, "Load BACnet Devices: ", 'bold')
    info_text.insert(tk.END, "Connect to the BACnet network and discover devices through Ethernet or Wi-Fi.\n\n")

    info_text.insert(tk.END, "Load BACnet Objects: ", 'bold')
    info_text.insert(tk.END, "Once a device is selected, objects will populate in the Object Display.\n\n")

    info_text.insert(tk.END, "Filter Objects: ", 'bold')
    info_text.insert(tk.END, "Use the Object Type Selection to choose what objects will show in the Object Display.\n\n")

    info_text.insert(tk.END, "Select Objects: ", 'bold')
    info_text.insert(tk.END, "Use the Select All button to select all objects on device.\n\n")

    info_text.insert(tk.END, "Deselect Objects: ", 'bold')
    info_text.insert(tk.END, "Use the Deselect All button to deselect all objects.\n\n")

    info_text.insert(tk.END, "Save File: ", 'bold')
    info_text.insert(tk.END, "Use the Save File button to save all selected objects to a new tags.txt and translate.ini file in the currently selected folder.\n\n")

    info_text.insert(tk.END, "Append File: ", 'bold')
    info_text.insert(tk.END, "Use the Append File button to save all selected objects to tags.txt and translate.ini file in the currently selected folder.\n\n")

    info_text.insert(tk.END, "Select Folder: ", 'bold')
    info_text.insert(tk.END, "Use the Folder button to choose which folder location the application will read/write from.\n\n")

    info_text.insert(tk.END, "Load Tags File: ", 'bold')
    info_text.insert(tk.END, "Use the Load Tags File button to populate the list with contents from any tags.txt file.\n\n")

    info_text.insert(tk.END, "Remove Objects(s): ", 'bold')
    info_text.insert(tk.END, "Use the Remove Object(s) button to delete the selected objects from tags.txt and translate.ini files.\n\n")

    info_text.insert(tk.END, "Write Objects to CSV: ", 'bold')
    info_text.insert(tk.END, "Use the Write Objects to CSV button to save all device objects to a CSV file in the currently selected folder. Similar to PDB Extractor.\n\n")

    info_text.insert(tk.END, "Use the tooltips on buttons for more instructions.\n\n", 'bold')
    info_text.insert(tk.END, "Enjoy managing your BACnet objects with ease!\n", 'bold')

    info_text.config(state='disabled')  # Make the text widget read-only
    info_text.pack(fill='both', expand=True)

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

# Open the image file with PIL.
# Two directories, because images are put in different directory when the script
# is compiled to an executable.
try:
    info_img = Image.open(resource_path('info.png'))
except:
    info_img = Image.open('icons/info.png')

# Resize the image with PIL
info_img = info_img.resize((20,20))

# Convert the PIL image object to a PhotoImage object
info_img = ImageTk.PhotoImage(info_img)

# Add the Information button
info_button = ttk.Button(frame3,width=3,image=info_img, command=show_information_window)
info_button.image = info_img
info_button.grid(row=0,column=1, sticky=(tk.E,tk.N))
folder_button_ttp = tt.CreateToolTip(info_button, \
    "Application Info.")

# Open the image file with PIL
try:
    folder_img = Image.open(resource_path('folder.png'))
except:
    folder_img = Image.open('icons/folder.png')


# Resize the image with PIL
folder_img = folder_img.resize((25, 25))

# Convert the PIL image object to a PhotoImage object
folder_img = ImageTk.PhotoImage(folder_img)

button_frame1 = ttk.Frame(frame3)
button_frame1.grid(row=5, column=0,padx=(0, 10),pady=(10,0),sticky=('WENS'))
button_frame1.grid_columnconfigure(0, weight=1)
button_frame1.grid_columnconfigure(1, weight=4)
button_frame1.grid_columnconfigure(2, weight=4)
button_frame1.grid_columnconfigure(3, weight=4)

button_frame2 = ttk.Frame(frame3)
button_frame2.grid(row=6, column=0,padx=(0, 10),pady=0, sticky=('WENS'))
button_frame2.grid_columnconfigure(0, weight=1)
button_frame2.grid_columnconfigure(1, weight=1)
button_frame2.grid_columnconfigure(2, weight=1)

button_frame3 = ttk.Frame(frame3)
button_frame3.grid(row=7, column=0,padx=(0, 15),pady=0, sticky=('WENS'))
button_frame3.grid_columnconfigure(0, weight=1)

# Add the Debug button
info_button = ttk.Button(button_frame3, text="Debug", command=show_debug_window)
info_button.grid(row=0,column=1, sticky=('E'))
folder_button_ttp = tt.CreateToolTip(info_button, "Debug Info.")

# Add the Save to Files button
folder_button = ttk.Button(button_frame1,image=folder_img, command=select_folder)
folder_button.image = folder_img
folder_button.grid(row=0, column=0,padx=5, sticky=('WENS'))
folder_button_ttp = tt.CreateToolTip(folder_button, \
    "Change folder location")

save_button = ttk.Button(button_frame1, text="Save File ", command=save_to_files)
save_button.grid(row=0, column=1,padx=5, sticky=('WENS'))
save_button_ttp = tt.CreateToolTip(save_button, \
    "Save objects to new 'tags.txt' and 'translate.ini' files")

append_button = ttk.Button(button_frame1, text="Append File", command=append_to_file)
append_button.grid(row=0, column=2,padx=5, sticky=('WENS'))
append_button_ttp = tt.CreateToolTip(append_button, \
    "Add selected objects to the 'tags.txt' and 'translate.ini' files")

remove_button = ttk.Button(button_frame1, text="Remove Object(s)",command=delete_selected_items)
remove_button.grid(row=0, column=3,padx=5, sticky=('WENS'))
remove_button_ttp = tt.CreateToolTip(remove_button, \
    "Remove selected objects from 'tags.txt' and 'translate.ini' files.")

def compare_files():
    global file_path

    # Open a file dialog to select the tags.txt file
    file_path = filedialog.askopenfilename(initialdir=default_folder, filetypes=[("Text files", "*.txt")])

    # Check if a file was selected
    if file_path:
        # Clear the comparison listbox
        comparison_listbox.delete(0, tk.END)

        # Open the file and read the objects
        with open(file_path, 'r') as file:
            reader = csv.reader(file, delimiter=',')
            for row in reader:
                # Insert each object into the comparison listbox
                comparison_listbox.insert(tk.END, f"{row[0]} - {row[2]}")

# Add the Compare Files button
compare_button = ttk.Button(button_frame2, text="Load Tags File", command=compare_files)
compare_button.grid(row=0, column=2,padx=(10,5), sticky='WENS')
compare_button_ttp = tt.CreateToolTip(compare_button, \
    "Select and load a 'tags.txt' file to populate the list with objects.")

def csv_read_objects_chunk(mac, device_id, object_chunk):
    print(f"csv_read_objects_chunk started")
    extra_bacnet_objects = [
        BacnetObject(mac, obj[0], obj[1], device_id)
        for obj in object_chunk
    ]
    if mac not in extra_objects_for_device:
        extra_objects_for_device[mac] = []
    extra_objects_for_device[mac].extend(extra_bacnet_objects)
    for obj in extra_bacnet_objects:
        print(f"Loaded object: {obj.deviceID}.{obj.objectIdentifier} - {obj.objectName}")

def csv_read_objects_for_device(mac, device_id):
    print("csv_read_objects_for_device started")
    try:
        object_list = bacnet.read(f'{mac} device {device_id} objectList')
        chunk_size = 10  # Define the chunk size
        threads = []

        for i in range(0, len(object_list), chunk_size):
            chunk = object_list[i:i + chunk_size]
            # Create a thread for each chunk
            thread = threading.Thread(target=csv_read_objects_chunk, args=(mac, device_id, chunk))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    except Exception as e:
        loading_label.config(text="")
        loading_label.update()
        print(f"Error reading objects for device {device_id}: {e}")

def csv_writer_thread(all_objects):
    # Define headers for the CSV file
    headers = ['Name', 'Object', 'ObjectType', 'Description', 'Value', 'Status']

    # Write the collected objects to a CSV file
    csv_file = f"{default_folder}/Controller Objects.csv"
    with open(csv_file, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # Write headers
        writer.writerows([[obj.objectName, obj.objectIdentifier, obj.objectType, obj.description, obj.presentValue, obj.status] for obj in all_objects])  # Write all collected objects

    # Notify the user
    tkinter.messagebox.showinfo(title='Info', message=f'Objects have been written to Controller Objects.csv.')
    loading_label.config(text="")
    loading_label.update()

def objects_to_csv():
    selected_device = device_var.get()
    tkinter.messagebox.showinfo(title='Info', message=f'{selected_device} will be written to csv.')
    loading_label.config(text="Loading CSV...")
    loading_label.update()
    print(f"selected_device: {selected_device}")
    for device_info in all_devices:
        device_name = f'{device_info[0]} ({device_info[3]})'
        print(f"device_name: {device_name}")
        if selected_device == device_name:
            mac = device_info[2]
            csv_read_objects_for_device(mac, device_info[3])
            all_objects = extra_objects_for_device[mac]
            break

    # Start the CSV writer in a new thread
    csv_thread = threading.Thread(target=csv_writer_thread, args=(all_objects,))
    csv_thread.start()

csv_button = ttk.Button(button_frame3, text="Write Objects to CSV",command=objects_to_csv)
csv_button.grid(row=0, column=0,padx=5, sticky=('WNS'))
csv_button_ttp = tt.CreateToolTip(csv_button, \
    "Exports all BACnet objects from device to a CSV file. Like PDB Extractor.")

def save_to_files_thread():
    global default_folder  # Declare the variable as global at the beginning of the function
    print("save_to_files_thread started")  # Debugging print statement
    selected = object_listbox.curselection()
    selected_objects = [object_listbox.get(i) for i in selected]

    # Map the selected strings back to BacnetObject instances
    selected_objects = [obj for obj in current_list if f"{obj.deviceID}.{obj.objectIdentifier} - {obj.objectName}" in selected_objects]

    # Create translate.ini
    translate_file_path = os.path.join(default_folder, 'translate.ini')
    with open(translate_file_path, 'wb') as file:
        file.write(b'[translate]\r\n')
        for obj in selected_objects:
            # Correctly access the deviceID property
            line = f'{obj.deviceID}.{obj.objectIdentifier}={obj.objectName}\r\n'
            file.write(line.encode())

    # Create tags.txt
    tags_file_path = os.path.join(default_folder, 'tags.txt')
    with open(tags_file_path, 'wb') as file:
        for obj in selected_objects:
            if obj.objectType == 'binaryValue':
                symbol = 'BOOL'
            else:
                symbol = '%'
            # Correctly access the deviceID property
            line = f'{obj.deviceID}.{obj.objectIdentifier},{symbol},{obj.objectName}\r\n'
            saved_objects.append(f'{obj.deviceID}.{obj.objectIdentifier},{symbol},{obj.objectName}')
            file.write(line.encode())
    tkinter.messagebox.showinfo(title='Info',message='File has been saved.')
    print("save_to_files_thread finished")  # Debugging print statement
    update_comparison_listbox()

def select_all():
    type_listbox.select_set(0, tk.END)
    update_object_listbox(object_listbox)
    object_listbox.select_set(0, tk.END)

def deselect_all():
    type_listbox.select_set(0, tk.END)
    update_object_listbox(object_listbox)
    object_listbox.select_clear(0,tk.END)

# Add the Select All button
select_all_button = ttk.Button(button_frame2, text="Select All", command=select_all)
select_all_button.grid(row=0, column=0, padx=(5,10), sticky='WENS')
select_all_button_ttp = tt.CreateToolTip(select_all_button, \
    "Select all objects on device.")

# Add the Select All button
select_all_button = ttk.Button(button_frame2, text="Deselect All", command=deselect_all)
select_all_button.grid(row=0, column=1, padx=(5,10), sticky='WENS')
select_all_button_ttp = tt.CreateToolTip(select_all_button, \
    "Deselect all objects.")

# Stdout-like class to redirect stdout to debug window on GUI
class Mystdout:
    def __init__(self):
        pass

    def write(self, inputStr):
        console_text.insert(tk.END, inputStr)
        console_text.see('end')

    def flush(self):
        pass

# Create and immediately withdraw the debug window, so that debug output
# can keep piling up for us to look in the future
def debug_window_init():
    create_debug_window()
    debug_window.withdraw()
    # The following line reassigns stdout to our stdout-like class
    mstdout = Mystdout()
    sys.stdout = mstdout
    # Also redirect all the output from modules that use "logging" module
    logging.basicConfig(stream=mstdout)
    # BAC0 is very verbose in DEBUG, so disable it
    logging.disable(level=logging.DEBUG)

root.after(100, debug_window_init)
root.after(500, Network_Connect)
root.mainloop()

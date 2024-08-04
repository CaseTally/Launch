import customtkinter as ctk
from tkinter import messagebox, filedialog, simpledialog, Menu, Scrollbar, Canvas, Frame, Text, END, INSERT, Toplevel, Label, Entry, Button, Listbox, IntVar, MULTIPLE
from tkinter import ttk 
import json
import os

# Initial parameters and weights
parameters = {
    "Case Duration": ["Less than 1 year", "1-2 years", "More than 2 years"],
    "Projected Cost": ["Under $25k", "$25k - $50k", "Over $50k"],
    "Total Case Hours": ["Under 100 Hrs", "100-300 Hrs", "More than 300 Hrs"],
    "Case Revenue": ["Small Case ( < 500k)", "Medium Case (500k-1M )", "Big Case ( > 1M )"],
    "Contingency Rate": ["25%", "33%", "40%"],
    "Case Complexity": ["Low", "Average", "High"],
    "Risk Exposure": ["Low", "Average", "High"],
    "Client Behavior": ["Low", "Average", "Great"]
}

weights = {
    "Case Duration": [70, 50, 30],  # Lower duration is better
    "Projected Cost": [70, 50, 30],  # Lower cost is better
    "Total Case Hours": [70, 50, 30],  # Lower hours are better
    "Case Revenue": [30, 50, 70],  # Higher revenue is better
    "Contingency Rate": [30, 50, 70],  # Higher contingency rate is better
    "Case Complexity": [70, 50, 30],  # Lower complexity is better
    "Risk Exposure": [70, 50, 30],  # Lower risk is better
    "Client Behavior": [30, 50, 70],  # Better client behavior is better
}

# Initial weights for status buttons
status_weights = {
    "Filed": 2,
    "Discovery": 4,
    "Deposition": 7,
    "Arbitration": 13,
    "Mediation": 22,
    "Settled": 30,
    "Trial": 9,
    "Await Decision": 1,
    "Decision": 2,
}

# Initial maximum number of active cases
max_active_cases = 30

# Weights for active case load grading
active_case_load_weights = weights.copy()

# Scroll bar color from the provided image
scrollbar_color = "#1C1C1C"  # Example color extracted from the image

# Store button references
button_references = {}

# Store button statuses for maintaining color state
button_statuses = {}

# Track the number of parameters to detect changes
previous_param_count = len(parameters)

# Function to calculate the grade based on the input values
def calculate_grade(case_data, weights):
    total_weight = sum([max(weights[key]) for key in case_data if key in weights])
    total_score = sum([weights[key][case_data[key]] for key in case_data if key in weights])
    normalized_score = (total_score / total_weight) * 100 if total_weight > 0 else 0
    return min(normalized_score, 100)  # Ensure the score does not exceed 100%

# Function to handle the grade button click
def on_grade():
    try:
        case_data = {param: parameters[param].index(button_statuses[param]) for param in parameters}
    except ValueError:
        messagebox.showerror("Input Error", "Please make sure all fields are filled in correctly.")
        return

    grade = calculate_grade(case_data, weights)
    grade_text = f"Overall Grade: {grade:.2f}%"
    
    if grade < 70:
        grade_label.configure(text=grade_text, text_color="red")
    elif 70 <= grade < 80:
        grade_label.configure(text=grade_text, text_color="yellow")
    elif 80 <= grade < 90:
        grade_label.configure(text=grade_text, text_color="light green")
    else:
        grade_label.configure(text=grade_text, text_color="green")
    
    if len(recent_entries) >= 50:
        messagebox.showwarning("Limit Reached", "Please clear the record of recent entries.")
    else:
        recent_entries.append((case_name_var.get(), date_var.get(), grade, str(grade_label.cget("text_color")), [button_statuses[param] for param in parameters]))
        update_recent_entries()

# Function to update the recent entries display
def update_recent_entries():
    for widget in recent_entries_frame.winfo_children():
        widget.destroy()

    for idx, entry in enumerate(recent_entries):
        entry_text = f"{entry[0]} ({entry[1]}): "
        grade_text = f"{entry[2]:.2f}%"
        detail_text = f" {' | '.join(entry[4])}"

        label = Text(recent_entries_frame, font=("Helvetica", 14), wrap="none", height=2, width=120, borderwidth=0, background=scrollbar_color)
        label.insert(INSERT, entry_text)
        label.insert(INSERT, grade_text, entry[3])  # Set grade color
        label.insert(INSERT, detail_text)
        label.tag_configure("red", foreground="red")
        label.tag_configure("yellow", foreground="yellow")
        label.tag_configure("light green", foreground="light green")
        label.tag_configure("green", foreground="green")
        label.configure(state="disabled")
        label.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

        button_frame = Frame(recent_entries_frame, bg=scrollbar_color)
        button_frame.grid(row=idx, column=1, padx=5, pady=2, sticky="e")

        delete_button = ctk.CTkButton(button_frame, text="Delete", command=lambda i=idx: delete_entry(i), font=("Helvetica", 12, "bold"), fg_color="#3958D8", text_color="white")
        delete_button.grid(row=0, column=0, padx=5, pady=2)
        add_button = ctk.CTkButton(button_frame, text="Add Case", command=lambda i=idx: add_case_to_active_load(i), font=("Helvetica", 12, "bold"), fg_color="#3958D8", text_color="white")
        add_button.grid(row=0, column=1, padx=5, pady=2)

# Function to delete an individual entry
def delete_entry(index):
    del recent_entries[index]
    update_recent_entries()

# Function to add a case to the active case load
def add_case_to_active_load(index):
    global max_active_cases
    case = recent_entries[index]
    required_fields = case[4]  # Only check the parameters, which are stored in case[4]
    if not all(required_fields):  # Check if all fields in the case are filled
        messagebox.showerror("Data Error", "Case data is incomplete. Please make sure all required fields are filled in.")
        return

    if len(active_case_load) >= max_active_cases:
        messagebox.showerror("Limit Reached", f"You cannot add more than {max_active_cases} cases to the active case load.")
    elif any(c == case for c in active_case_load):  # Compare by exact match of the entire case data
        messagebox.showerror("Duplicate Case", "This case is already in the active case load.")
    else:
        active_case_load.append(case)
        update_active_case_load()

# Function to reset button colors for a specific case
def reset_button_colors(case_index):
    for status in ["Filed", "Discovery", "Deposition", "Arbitration", "Mediation", "Settled", "Trial", "Await Decision", "Decision"]:
        if (case_index, status) in button_references:
            button_references[(case_index, status)].configure(fg_color="#3958D8", text_color="white")
            button_statuses[(case_index, status)] = ("#3958D8", "white")

# Function to update the status of a case
def update_status(case_index, status):
    try:
        active_case_load[case_index] = list(active_case_load[case_index])  # Convert to list for mutability
        while len(active_case_load[case_index]) < 6:
            active_case_load[case_index].append("")
        active_case_load[case_index][5] = status  # Update status
        active_case_load[case_index] = tuple(active_case_load[case_index])  # Convert back to tuple

        reset_button_colors(case_index)  # Reset button colors for this case

        if (case_index, status) in button_references:
            selected_button = button_references[(case_index, status)]
            if status in ["Filed", "Discovery", "Deposition"]:
                selected_button.configure(fg_color="red", text_color="white")  # Red for Filed to Deposition
                button_statuses[(case_index, status)] = ("red", "white")
            elif status in ["Arbitration", "Mediation", "Settled"]:
                selected_button.configure(fg_color="yellow", text_color="black")  # Yellow for Arbitration to Settled
                button_statuses[(case_index, status)] = ("yellow", "black")
            elif status in ["Trial", "Await Decision", "Decision"]:
                selected_button.configure(fg_color="green", text_color="white")  # Green for Trial to Decision
                button_statuses[(case_index, status)] = ("green", "white")

        adjust_weights_for_status(case_index, status)  # Adjust weights based on status
        update_active_case_load()  # Ensure grade is updated whenever status changes
    except Exception as e:
        print(f"Error updating status: {e}")

# Function to adjust weights based on the status
def adjust_weights_for_status(case_index, status):
    factor = status_weights.get(status, 1.0)
    for param in active_case_load_weights:
        active_case_load_weights[param] = [int(w * factor) for w in weights[param]]

    update_active_case_load()

# Function to update the active case load display
def update_active_case_load():
    for widget in active_case_load_frame.winfo_children():
        widget.destroy()

    if active_case_load:
        try:
            avg_grade = sum(
                calculate_grade(
                    {param: parameters[param].index(case_data) for param, case_data in zip(parameters.keys(), case[4]) if param in parameters},
                    active_case_load_weights
                ) for case in active_case_load
            ) / len(active_case_load)
            active_case_load_grade_label.configure(text=f"Active Case Load Grade: {avg_grade:.2f}%")
            if avg_grade < 70:
                active_case_load_grade_label.configure(text_color="red")
            elif 70 <= avg_grade < 80:
                active_case_load_grade_label.configure(text_color="yellow")
            elif 80 <= avg_grade < 90:
                active_case_load_grade_label.configure(text_color="light green")
            else:
                active_case_load_grade_label.configure(text_color="green")
        except ValueError as e:
            print("Error calculating average grade:", e)
            print("Active case load data:", active_case_load)
            messagebox.showerror("Data Error", "There is an error in the case data. Please check the inputs.")
    else:
        active_case_load_grade_label.configure(text="Grade: 0.00%", text_color="white")  # Reset grade when no active cases
    
    for idx, case in enumerate(active_case_load):
        entry_text = f"{case[0]} ({case[1]}): "
        grade_text = f"{case[2]:.2f}%"
        detail_text = f" {' | '.join(case[4])}"

        label = Text(active_case_load_frame, font=("Helvetica", 14), wrap="none", height=2, width=100, borderwidth=0, background=scrollbar_color)
        label.insert(INSERT, entry_text)
        label.insert(INSERT, grade_text, case[3])  # Set grade color
        label.insert(INSERT, detail_text)
        label.tag_configure("red", foreground="red")
        label.tag_configure("yellow", foreground="yellow")
        label.tag_configure("light green", foreground="light green")
        label.tag_configure("green", foreground="green")
        label.configure(state="disabled")
        label.grid(row=idx, column=0, sticky="ew", padx=5, pady=2)

        # Button frame inside the label for status buttons
        button_frame = Frame(active_case_load_frame, bg=scrollbar_color)
        button_frame.grid(row=idx, column=1, padx=5, pady=2, sticky="e")

        # Add status buttons inside the same grid
        statuses = ["Filed", "Discovery", "Deposition", "Arbitration", "Mediation", "Settled", "Trial", "Await Decision", "Decision"]
        for status in statuses:
            status_button = ctk.CTkButton(button_frame, text=status, command=lambda s=status, i=idx: update_status(i, s), font=("Helvetica", 12), width=10, fg_color="#3958D8", text_color="white")
            status_button.grid(row=0, column=statuses.index(status), padx=2)

            # Store button reference
            button_references[(idx, status)] = status_button

            # Restore button color if previously set
            if (idx, status) in button_statuses:
                status_button.configure(fg_color=button_statuses[(idx, status)][0], text_color=button_statuses[(idx, status)][1])

        delete_button = ctk.CTkButton(button_frame, text="Delete", command=lambda i=idx: delete_active_case(i), font=("Helvetica", 12, "bold"), fg_color="#3958D8", text_color="white")
        delete_button.grid(row=0, column=len(statuses), padx=5, pady=2)
        case_over_button = ctk.CTkButton(button_frame, text="Case Over", command=lambda i=idx: mark_case_over(i), font=("Helvetica", 12, "bold"), fg_color="#3958D8", text_color="white")
        case_over_button.grid(row=0, column=len(statuses) + 1, padx=5, pady=2)

# Function to delete an individual active case
def delete_active_case(index):
    del active_case_load[index]
    update_active_case_load()

# Function to clear the receipt area
def clear_receipt():
    for param in button_statuses:
        button_statuses[param] = ""
        refresh_button_color(param)
    grade_label.configure(text="Overall Grade: ", text_color="white")

# Function to clear the recent entries
def clear_recent_entries():
    recent_entries.clear()
    update_recent_entries()
    active_case_load.clear()  # Clear active cases
    update_active_case_load()  # Reset grade

# Function to extract records to a text file
def extract_records():
    headers = ["Case Name", "Date", "Grade", "Grade Color"] + list(parameters.keys())
    records = ["\t".join(headers)]  # Add headers
    for entry in recent_entries:
        record = [entry[0], entry[1], f"{entry[2]:.2f}%", str(entry[3])] + entry[4]
        records.append("\t".join(record))
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
    if file_path:
        with open(file_path, "w") as file:
            for record in records:
                file.write(record + "\n")
        messagebox.showinfo("Success", "Records have been extracted successfully!")

# Function to toggle the active case load
def toggle_active_case_load():
    if active_case_load_container.winfo_ismapped():
        active_case_load_container.grid_remove()
    else:
        active_case_load_container.grid()
        update_active_case_load()

# Function to handle parameter selection
def select_parameter(param, option):
    button_statuses[param] = option
    refresh_button_color(param)

# Function to adjust the maximum number of active cases
def adjust_max_active_cases():
    global max_active_cases
    max_cases = simpledialog.askinteger("Input", "Set maximum number of active cases:", minvalue=1, maxvalue=100, initialvalue=max_active_cases)
    if max_cases is not None:
        max_active_cases = max_cases

# Function to save weights to a preset
def save_preset(weights):
    preset_name = simpledialog.askstring("Preset Name", "Enter the name for the preset:")
    if preset_name:
        with open(f"{preset_name}_weights.json", "w") as f:
            json.dump(weights, f)
        update_presets_menu()
        messagebox.showinfo("Success", f"Preset '{preset_name}' saved successfully!")

# Function to show a popup window to adjust weights
def adjust_weights_popup(title, weights, save_function):
    def save_and_close():
        for param, entry_list in entries.items():
            weights[param] = [int(entry.get()) for entry in entry_list]
        save_function()
        popup.destroy()
        messagebox.showinfo("Success", "Weights adjusted successfully!")

    def save_weights_preset():
        save_preset(weights)
    
    popup = Toplevel(root)
    popup.title(title)
    entries = {}
    for idx, (param, weight_list) in enumerate(weights.items()):
        Label(popup, text=param, font=("Helvetica", 12)).grid(row=idx, column=0, padx=5, pady=5)
        entries[param] = []
        for w_idx, weight in enumerate(weight_list):
            entry = Entry(popup, width=5)
            entry.insert(END, weight)
            entry.grid(row=idx, column=w_idx+1, padx=5, pady=5)
            entries[param].append(entry)
    Button(popup, text="Save", command=save_and_close).grid(row=len(weights), column=0, columnspan=2, pady=10)
    Button(popup, text="Save as Preset", command=save_weights_preset).grid(row=len(weights), column=2, columnspan=2, pady=10)

# Function to adjust active case load grade factors
def adjust_active_case_load_grade_factors():
    adjust_weights_popup("Adjust Active Case Load Grade Factors", active_case_load_weights, save_active_case_load_weights)

# Function to adjust calculator weights
def adjust_calculator_weights():
    adjust_weights_popup("Adjust Calculator Weights", weights, save_weights)

# Function to adjust status button weights
def adjust_status_weights():
    def save_status_weights():
        for status, entry in entries.items():
            status_weights[status] = float(entry.get())
        save_weights_status()
        popup.destroy()
        messagebox.showinfo("Success", "Status weights adjusted successfully!")
    
    def save_weights_status():
        with open("status_weights.json", "w") as f:
            json.dump(status_weights, f)

    popup = Toplevel(root)
    popup.title("Adjust Status Button Weights")
    entries = {}
    for idx, (status, weight) in enumerate(status_weights.items()):
        Label(popup, text=status, font=("Helvetica", 12)).grid(row=idx, column=0, padx=5, pady=5)
        entry = Entry(popup, width=5)
        entry.insert(END, weight)
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[status] = entry
    Button(popup, text="Save", command=save_status_weights).grid(row=len(status_weights), column=0, columnspan=2, pady=10)

# Function to save active case load weights to a file
def save_active_case_load_weights():
    with open("active_case_load_weights.json", "w") as f:
        json.dump(active_case_load_weights, f)

# Function to load active case load weights from a file
def load_active_case_load_weights():
    global active_case_load_weights
    try:
        with open("active_case_load_weights.json", "r") as f:
            active_case_load_weights = json.load(f)
    except FileNotFoundError:
        pass

# Function to delete a preset
def delete_preset(preset_name):
    try:
        os.remove(f"{preset_name}_weights.json")
        update_presets_menu()
        messagebox.showinfo("Success", f"Preset '{preset_name}' deleted successfully!")
    except FileNotFoundError:
        messagebox.showerror("Error", f"Preset '{preset_name}' not found.")

# Function to load weights from a preset
def load_preset(preset_name):
    global weights
    try:
        with open(f"{preset_name}_weights.json", "r") as f:
            weights = json.load(f)
        messagebox.showinfo("Success", f"Preset '{preset_name}' loaded successfully!")
    except FileNotFoundError:
        messagebox.showerror("Error", f"Preset '{preset_name}' not found.")

# Function to update presets menu
def update_presets_menu():
    presets_menu.delete(0, END)
    presets = [f.split('_weights.json')[0] for f in os.listdir() if f.endswith('_weights.json')]
    for preset in presets:
        presets_menu.add_command(label=preset, command=lambda p=preset: load_preset(p))

# Function to add a new row to the calculator
def add_new_row():
    def confirm_add_row():
        row_name = row_name_entry.get()
        button_names = [button_name_1_entry.get(), button_name_2_entry.get(), button_name_3_entry.get()]
        try:
            weights = [int(weight_1_entry.get()), int(weight_2_entry.get()), int(weight_3_entry.get())]
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid weights.")
            return

        parameters[row_name] = button_names
        active_case_load_weights[row_name] = weights
        button_statuses[row_name] = ""

        refresh_calculator_setup()
        row_popup.destroy()
        messagebox.showinfo("Success", "New row added successfully!")

    row_popup = Toplevel(root)
    row_popup.title("Add New Row")
    Label(row_popup, text="Row Name", font=("Helvetica", 12)).grid(row=0, column=0, padx=5, pady=5)
    row_name_entry = Entry(row_popup, font=("Helvetica", 12))
    row_name_entry.grid(row=0, column=1, padx=5, pady=5)
    
    Label(row_popup, text="Button Name 1", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5)
    button_name_1_entry = Entry(row_popup, font=("Helvetica", 12))
    button_name_1_entry.grid(row=1, column=1, padx=5, pady=5)
    
    Label(row_popup, text="Button Name 2", font=("Helvetica", 12)).grid(row=2, column=0, padx=5, pady=5)
    button_name_2_entry = Entry(row_popup, font=("Helvetica", 12))
    button_name_2_entry.grid(row=2, column=1, padx=5, pady=5)
    
    Label(row_popup, text="Button Name 3", font=("Helvetica", 12)).grid(row=3, column=0, padx=5, pady=5)
    button_name_3_entry = Entry(row_popup, font=("Helvetica", 12))
    button_name_3_entry.grid(row=3, column=1, padx=5, pady=5)

    Label(row_popup, text="Weight 1", font=("Helvetica", 12)).grid(row=4, column=0, padx=5, pady=5)
    weight_1_entry = Entry(row_popup, font=("Helvetica", 12))
    weight_1_entry.grid(row=4, column=1, padx=5, pady=5)

    Label(row_popup, text="Weight 2", font=("Helvetica", 12)).grid(row=5, column=0, padx=5, pady=5)
    weight_2_entry = Entry(row_popup, font=("Helvetica", 12))
    weight_2_entry.grid(row=5, column=1, padx=5, pady=5)

    Label(row_popup, text="Weight 3", font=("Helvetica", 12)).grid(row=6, column=0, padx=5, pady=5)
    weight_3_entry = Entry(row_popup, font=("Helvetica", 12))
    weight_3_entry.grid(row=6, column=1, padx=5, pady=5)

    Button(row_popup, text="Add Row", command=confirm_add_row).grid(row=7, column=0, padx=5, pady=5)
    Button(row_popup, text="Cancel", command=lambda: row_popup.destroy()).grid(row=7, column=1, padx=5, pady=5)

# Function to refresh the calculator setup after adding or deleting a row
def refresh_calculator_setup():
    global previous_param_count
    for widget in calculator_frame.winfo_children():
        widget.destroy()

    row = 0
    for param, options in parameters.items():
        ctk.CTkLabel(calculator_frame, text=param, font=font_large).grid(row=row, column=0, sticky="w", padx=5, pady=5)
        col = 1
        button_references[param] = {}
        for option in options:
            button = ctk.CTkButton(calculator_frame, text=option, command=lambda p=param, o=option: select_parameter(p, o), font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
            button.grid(row=row, column=col, sticky="w", padx=5, pady=5)
            button_references[param][option] = button
            col += 1
        row += 1

    clear_receipt_button = ctk.CTkButton(calculator_frame, text="Clear Receipt", command=clear_receipt, font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
    clear_receipt_button.grid(row=row, column=0, sticky="w", padx=5, pady=5)

    global grade_label
    global grade_button

    grade_button = ctk.CTkButton(calculator_frame, text="GRADE", command=on_grade, font=("Helvetica", 16, "bold"), width=180, fg_color="#3958D8", text_color="white")
    grade_button.grid(row=row, column=1, sticky="w", padx=5, pady=5)

    grade_label = ctk.CTkLabel(calculator_frame, text="Overall Grade: ", font=("Helvetica", 16), anchor="w", text_color="white")
    grade_label.grid(row=row, column=2, sticky="w", padx=5, pady=5)

    # Check if the number of parameters has changed
    current_param_count = len(parameters)
    if current_param_count != previous_param_count:
        previous_param_count = current_param_count

def refresh_button_color(param):
    options = parameters[param]
    for option in options:
        button = button_references[param][option]
        if button_statuses[param] == option:
            button.configure(fg_color="white", text_color="black")  # Highlight selected button
        else:
            button.configure(fg_color="#3958D8", text_color="white")  # Set default color for unselected buttons

# Function to add extra input text bars
extra_input_labels = []
extra_input_entries = []

def add_extra_input():
    if len(extra_input_labels) < 10:
        input_num = len(extra_input_labels) + 1
        extra_input_label = ctk.CTkLabel(input_frame, text=f"Extra Input {input_num}", font=font_large)
        extra_input_entry = ctk.CTkEntry(input_frame, font=font_medium, width=400)
        extra_input_label.grid(row=2 + input_num, column=0, sticky="w", padx=5, pady=5)
        extra_input_entry.grid(row=2 + input_num, column=1, columnspan=3, sticky="w", padx=5, pady=5)
        extra_input_labels.append(extra_input_label)
        extra_input_entries.append(extra_input_entry)

# Function to customize calculator setup
def customize_calculator_setup():
    popup = Toplevel(root)
    popup.title("Customize Calculator Setup")

    add_row_button = Button(popup, text="Add New Row", command=add_new_row)
    add_row_button.grid(row=0, column=0, padx=5, pady=5)

    extra_input_button = Button(popup, text="Add Extra Input Text Bar", command=add_extra_input)
    extra_input_button.grid(row=1, column=0, padx=5, pady=5)

    customize_names_button = Button(popup, text="Customize Names", command=customize_calculator_names)
    customize_names_button.grid(row=2, column=0, padx=5, pady=5)
    
    delete_rows_button = Button(popup, text="Delete Rows", command=delete_rows)
    delete_rows_button.grid(row=4, column=0, padx=5, pady=5)

    save_case_load_var = IntVar()
    save_case_load_checkbox = Checkbutton(popup, text="Save Case Load", variable=save_case_load_var)
    save_case_load_checkbox.grid(row=3, column=0, padx=5, pady=5)

    popup.grid(row=0, column=0, padx=5, pady=5)

# Function to save weights to a file
def save_weights():
    with open("weights.json", "w") as f:
        json.dump(weights, f)

# Function to load weights from a file
def load_weights():
    global weights
    try:
        with open("weights.json", "r") as f:
            weights = json.load(f)
    except FileNotFoundError:
        pass

# Load weights on startup
load_weights()

# GUI setup
ctk.set_appearance_mode("dark")  # Changed back to "dark" mode
ctk.set_default_color_theme("dark-blue")  # Changed back to "dark-blue" theme

root = ctk.CTk()
root.title("Legal Case Calculator")
root.geometry("1900x1200")  # Adjusted size

# Font settings
font_large = ("Helvetica", 16)
font_medium = ("Helvetica", 14)
font_small = ("Helvetica", 12)

# Variables to store the selected values
recent_entries = []
active_case_load = []
button_statuses = {param: "" for param in parameters}

# Create a frame for the input fields
input_frame = ctk.CTkFrame(root)
input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

# Create a frame for the calculator buttons and labels
calculator_frame = ctk.CTkFrame(root)
calculator_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")

# Entry for Case Name
case_name_var = ctk.StringVar()
case_name_label = ctk.CTkLabel(input_frame, text="Case Name", font=font_large)
case_name_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
case_name_entry = ctk.CTkEntry(input_frame, textvariable=case_name_var, font=font_medium, width=400)
case_name_entry.grid(row=0, column=1, columnspan=3, sticky="w", padx=5, pady=5)

# Entry for Date
date_var = ctk.StringVar()
date_label = ctk.CTkLabel(input_frame, text="Date", font=font_large)
date_label.grid(row=1, column=0, sticky="w", padx=5, pady=5)
date_entry = ctk.CTkEntry(input_frame, textvariable=date_var, font=font_medium, width=400)
date_entry.grid(row=1, column=1, columnspan=3, sticky="w", padx=5, pady=5)

# Add buttons for each parameter directly next to the labels
row = 0
category_labels = {}
for param, options in parameters.items():
    param_label = ctk.CTkLabel(calculator_frame, text=param, font=font_large)
    param_label.grid(row=row, column=0, sticky="w", padx=5, pady=5)
    category_labels[param] = param_label
    col = 1
    button_references[param] = {}
    for option in options:
        button = ctk.CTkButton(calculator_frame, text=option, command=lambda p=param, o=option: select_parameter(p, o), font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
        button.grid(row=row, column=col, sticky="w", padx=5, pady=5)
        button_references[param][option] = button
        col += 1
    row += 1

# Clear receipt button
clear_receipt_button = ctk.CTkButton(calculator_frame, text="Clear Receipt", command=clear_receipt, font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
clear_receipt_button.grid(row=row, column=0, sticky="w", padx=5, pady=5)

# Grade button and label for the overall grade
grade_button = ctk.CTkButton(calculator_frame, text="GRADE", command=on_grade, font=("Helvetica", 16, "bold"), width=180, fg_color="#3958D8", text_color="white")
grade_button.grid(row=row, column=1, sticky="w", padx=5, pady=5)

global grade_label
grade_label = ctk.CTkLabel(calculator_frame, text="Overall Grade: ", font=("Helvetica", 16), anchor="w", text_color="white")
grade_label.grid(row=row, column=2, sticky="w", padx=5, pady=5)

# Create scrollable frame for recent entries
def create_scrollable_frame(root, row, column, colspan, padx=10, pady=5, height=150):
    container = Frame(root)
    canvas = Canvas(container, width=1700, height=height, bg=scrollbar_color)
    scrollbar = Scrollbar(container, orient="vertical", command=canvas.yview, bg=scrollbar_color)
    scrollable_frame = Frame(canvas, bg=scrollbar_color)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(
            scrollregion=canvas.bbox("all")
        )
    )

    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    container.grid(row=row, column=column, columnspan=colspan, sticky="nsew", padx=padx, pady=pady)
    canvas.grid(row=0, column=0, sticky="nsew")
    scrollbar.grid(row=0, column=1, sticky="ns")

    return scrollable_frame

# Create a container for calculator record components
calculator_record_container = ctk.CTkFrame(root, fg_color=scrollbar_color)
calculator_record_container.grid(row=row + 2, column=0, columnspan=6, sticky="nsew", padx=10, pady=5)

# Create scrollable frame for recent entries within the container
recent_entries_frame = create_scrollable_frame(calculator_record_container, 0, 0, 6, height=150)

# Pane for buttons in the calculator record area
button_pane_calculator = Frame(calculator_record_container, bg=scrollbar_color)
button_pane_calculator.grid(row=1, column=0, columnspan=6, sticky="nsew")

# Clear recent entries button
clear_recent_entries_button = ctk.CTkButton(button_pane_calculator, text="Clear Recent Entries", command=clear_recent_entries, font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
clear_recent_entries_button.grid(row=0, column=0, sticky="w", padx=10, pady=5)

# Extract records button
extract_button = ctk.CTkButton(button_pane_calculator, text="Extract", command=extract_records, font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
extract_button.grid(row=0, column=1, sticky="w", padx=10, pady=5)

# Create a container for active case load components
active_case_load_container = ctk.CTkFrame(root, fg_color=scrollbar_color)
active_case_load_container.grid(row=row + 4, column=0, columnspan=6, sticky="nsew", padx=10, pady=5)

# Active case load label
case_load_label = ctk.CTkLabel(active_case_load_container, text="Active Case Load", font=("Helvetica", 24))
case_load_label.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=5)

# Active case load grade label
active_case_load_grade_label = ctk.CTkLabel(active_case_load_container, text="Grade: 0.00%", font=("Helvetica", 24), text_color="white")
active_case_load_grade_label.grid(row=0, column=3, columnspan=4, sticky="w", padx=10, pady=5)

# Create scrollable frame for active case load
active_case_load_frame = create_scrollable_frame(active_case_load_container, 1, 0, 6, height=150)

# Extract button for active case load records
extract_button_active_cases = ctk.CTkButton(active_case_load_container, text="Extract Active Cases", command=extract_records, font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
extract_button_active_cases.grid(row=2, column=0, sticky="w", padx=10, pady=5)

# Menu bar for weight adjustments and toggling inputs
def open_settings_window():
    settings_window = Toplevel(root)
    settings_window.title("Settings")

    tab_control = ttk.Notebook(settings_window)
    calculator_customization_tab = ttk.Frame(tab_control)
    calculator_factors_tab = ttk.Frame(tab_control)
    grade_factors_tab = ttk.Frame(tab_control)
    presets_tab = ttk.Frame(tab_control)

    tab_control.add(calculator_customization_tab, text="Calculator Customization")
    tab_control.add(calculator_factors_tab, text="Calculator Factors")
    tab_control.add(grade_factors_tab, text="Grade Factors")
    tab_control.add(presets_tab, text="Presets")

    tab_control.pack(expand=1, fill="both")

    # Add content to tabs
    add_row_button = Button(calculator_customization_tab, text="Add New Row", command=add_new_row)
    add_row_button.grid(row=0, column=0, padx=5, pady=5)

    delete_rows_button = Button(calculator_customization_tab, text="Delete Rows", command=delete_rows)
    delete_rows_button.grid(row=1, column=0, padx=5, pady=5)

    customize_names_button = Button(calculator_customization_tab, text="Customize Names", command=customize_calculator_names)
    customize_names_button.grid(row=2, column=0, padx=5, pady=5)

    add_text_bar_button = Button(calculator_customization_tab, text="Add Extra Input Text Bar", command=add_extra_input)
    add_text_bar_button.grid(row=3, column=0, padx=5, pady=5)

    adjust_calculator_weights_button = Button(calculator_factors_tab, text="Adjust Calculator Weights", command=adjust_calculator_weights)
    adjust_calculator_weights_button.grid(row=0, column=0, padx=5, pady=5)

    adjust_active_case_load_grade_factors_button = Button(grade_factors_tab, text="Adjust Active Case Load Grade Factors", command=adjust_active_case_load_grade_factors)
    adjust_active_case_load_grade_factors_button.grid(row=0, column=0, padx=5, pady=5)

    adjust_status_weights_button = Button(grade_factors_tab, text="Adjust Status Button Weights", command=adjust_status_weights)
    adjust_status_weights_button.grid(row=1, column=0, padx=5, pady=5)

    tab_control.grid(row=0, column=0, padx=5, pady=5)

    global presets_menu  # Declare presets_menu as global
    presets_menu = Menu(presets_tab, tearoff=0)
    update_presets_menu()  # Initialize presets menu
    presets_tab.grid_rowconfigure(0, weight=1)
    presets_tab.grid_columnconfigure(0, weight=1)
    presets_listbox = Listbox(presets_tab)
    presets_listbox.grid(row=0, column=0, sticky="nsew")

    delete_preset_button = Button(presets_tab, text="Delete Preset", command=lambda: delete_preset(simpledialog.askstring("Delete Preset", "Enter the name of the preset to delete:")))
    delete_preset_button.grid(row=1, column=0, padx=5, pady=5)

def create_menu(root):
    menu_bar = Menu(root)

    settings_menu = Menu(menu_bar, tearoff=0)
    settings_menu.add_command(label="Open Settings", command=open_settings_window)
    menu_bar.add_cascade(label="Settings", menu=settings_menu)

    root.config(menu=menu_bar)

# Function to customize calculator names
def customize_calculator_names():
    global entries, button_name_entries
    popup = Toplevel(root)
    popup.title("Customize Names")

    entries = {}

    # Section for input text bars
    Label(popup, text="Input Text Bars", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=2, padx=5, pady=5)

    Label(popup, text="Case Name", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5)
    case_name_entry = Entry(popup, font=("Helvetica", 12))
    case_name_entry.insert(END, case_name_label.cget("text"))
    case_name_entry.grid(row=1, column=1, padx=5, pady=5)
    entries["Case Name"] = case_name_entry

    Label(popup, text="Date", font=("Helvetica", 12)).grid(row=2, column=0, padx=5, pady=5)
    date_entry = Entry(popup, font=("Helvetica", 12))
    date_entry.insert(END, date_label.cget("text"))
    date_entry.grid(row=2, column=1, padx=5, pady=5)
    entries["Date"] = date_entry

    # Add extra input bars if any
    for i, label in enumerate(extra_input_labels):
        label_text = label.cget("text")
        Label(popup, text=label_text, font=("Helvetica", 12)).grid(row=3 + i, column=0, padx=5, pady=5)
        extra_input_entry = extra_input_entries[i]
        entry = Entry(popup, font=("Helvetica", 12))
        entry.insert(END, extra_input_entry.get())
        entry.grid(row=3 + i, column=1, padx=5, pady=5)
        entries[label_text] = entry

    # Section for calculator category names
    Label(popup, text="Calculator Categories", font=("Helvetica", 14, "bold")).grid(row=4 + len(extra_input_labels), column=0, columnspan=2, padx=5, pady=5)

    for idx, param in enumerate(parameters.keys(), start=5 + len(extra_input_labels)):
        Label(popup, text=param, font=("Helvetica", 12)).grid(row=idx, column=0, padx=5, pady=5)
        entry = Entry(popup, font=("Helvetica", 12))
        entry.insert(END, category_labels[param].cget("text"))
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[param] = entry

    # Section for button names
    Label(popup, text="Category Button Names", font=("Helvetica", 14, "bold")).grid(row=4 + len(extra_input_labels), column=2, columnspan=3, padx=5, pady=5)

    button_name_entries = {param: [Entry(popup, font=("Helvetica", 12)) for _ in options] for param, options in parameters.items()}
    for idx, (param, options) in enumerate(parameters.items()):
        Label(popup, text=f"{param} Button Names", font=("Helvetica", 12)).grid(row=5 + idx + len(extra_input_labels), column=2, padx=5, pady=5)
        for btn_idx, option in enumerate(options):
            entry = button_name_entries[param][btn_idx]
            entry.insert(END, option)
            entry.grid(row=5 + idx + len(extra_input_labels), column=3 + btn_idx, padx=5, pady=5)

    # Adjust the row number for the Save button to ensure it's visible
    Button(popup, text="Save", command=save_names).grid(row=6 + len(parameters) + len(extra_input_labels), column=0, columnspan=5, pady=10)

    Button(popup, text="Refresh", command=lambda: refresh_customization_window(popup)).grid(row=6 + len(parameters) + len(extra_input_labels), column=5, columnspan=5, pady=10)

def save_names():
    global entries, button_name_entries
    for key, entry in entries.items():
        new_name = entry.get()
        if new_name and new_name != key:
            # Update input text bar descriptions only
            if key == "Case Name":
                case_name_label.configure(text=new_name)
            elif key == "Date":
                date_label.configure(text=new_name)
            # Update calculator categories
            elif key in parameters:
                category_labels[key].configure(text=new_name)

    # Update button names for each parameter
    for param, btn_entries in button_name_entries.items():
        parameters[param] = [btn_entry.get() for btn_entry in btn_entries]
    
    update_gui_texts()
    messagebox.showinfo("Success", "Names customized successfully!")

def update_gui_texts():
    # Update the text bars (Case Name and Date) descriptions only
    for key, entry in entries.items():
        new_label_text = entry.get()
        if key == "Case Name":
            case_name_label.configure(text=new_label_text)
        elif key == "Date":
            date_label.configure(text=new_label_text)
        else:
            for idx, label in enumerate(extra_input_labels):
                if label.cget("text") == key:
                    extra_input_labels[idx].configure(text=new_label_text)

    # Update the main parameters and buttons
    for param, options in parameters.items():
        col = 1
        for option in options:
            if param in button_references and option in button_references[param]:
                button = button_references[param][option]
                button.configure(text=option)
            else:
                # Create a new button if it doesn't exist
                button = ctk.CTkButton(calculator_frame, text=option, command=lambda p=param, o=option: select_parameter(p, o), font=("Helvetica", 12, "bold"), width=180, fg_color="#3958D8", text_color="white")
                button.grid(row=list(parameters.keys()).index(param), column=col, sticky="w", padx=5, pady=5)
                if param not in button_references:
                    button_references[param] = {}
                button_references[param][option] = button
            col += 1

def refresh_customization_window(popup):
    global entries, button_name_entries

    # Clear current entries
    for key in list(entries.keys()):
        entries[key].destroy()
    for key in list(button_name_entries.keys()):
        for entry in button_name_entries[key]:
            entry.destroy()
    
    entries = {}

    # Section for input text bars
    Label(popup, text="Input Text Bars", font=("Helvetica", 14, "bold")).grid(row=0, column=0, columnspan=2, padx=5, pady=5)

    Label(popup, text="Case Name", font=("Helvetica", 12)).grid(row=1, column=0, padx=5, pady=5)
    case_name_entry = Entry(popup, font=("Helvetica", 12))
    case_name_entry.insert(END, case_name_label.cget("text"))
    case_name_entry.grid(row=1, column=1, padx=5, pady=5)
    entries["Case Name"] = case_name_entry

    Label(popup, text="Date", font=("Helvetica", 12)).grid(row=2, column=0, padx=5, pady=5)
    date_entry = Entry(popup, font=("Helvetica", 12))
    date_entry.insert(END, date_label.cget("text"))
    date_entry.grid(row=2, column=1, padx=5, pady=5)
    entries["Date"] = date_entry

    # Add extra input bars if any
    for i, label in enumerate(extra_input_labels):
        label_text = label.cget("text")
        Label(popup, text=label_text, font=("Helvetica", 12)).grid(row=3 + i, column=0, padx=5, pady=5)
        extra_input_entry = extra_input_entries[i]
        entry = Entry(popup, font=("Helvetica", 12))
        entry.insert(END, extra_input_entry.get())
        entry.grid(row=3 + i, column=1, padx=5, pady=5)
        entries[label_text] = entry

    # Section for calculator category names
    Label(popup, text="Calculator Categories", font=("Helvetica", 14, "bold")).grid(row=4 + len(extra_input_labels), column=0, columnspan=2, padx=5, pady=5)

    for idx, param in enumerate(parameters.keys(), start=5 + len(extra_input_labels)):
        Label(popup, text=param, font=("Helvetica", 12)).grid(row=idx, column=0, padx=5, pady=5)
        entry = Entry(popup, font=("Helvetica", 12))
        entry.insert(END, category_labels[param].cget("text"))
        entry.grid(row=idx, column=1, padx=5, pady=5)
        entries[param] = entry

    # Section for button names
    Label(popup, text="Category Button Names", font=("Helvetica", 14, "bold")).grid(row=4 + len(extra_input_labels), column=2, columnspan=3, padx=5, pady=5)

    button_name_entries = {param: [Entry(popup, font=("Helvetica", 12)) for _ in options] for param, options in parameters.items()}
    for idx, (param, options) in enumerate(parameters.items()):
        Label(popup, text=f"{param} Button Names", font=("Helvetica", 12)).grid(row=5 + idx + len(extra_input_labels), column=2, padx=5, pady=5)
        for btn_idx, option in enumerate(options):
            entry = button_name_entries[param][btn_idx]
            entry.insert(END, option)
            entry.grid(row=5 + idx + len(extra_input_labels), column=3 + btn_idx, padx=5, pady=5)

    Button(popup, text="Save", command=save_names).grid(row=6 + len(parameters) + len(extra_input_labels), column=0, columnspan=5, pady=10)

# Function to delete rows
def delete_rows():
    popup = Toplevel(root)
    popup.title("Delete Rows")

    listbox = Listbox(popup, selectmode=MULTIPLE, font=("Helvetica", 12))
    for param in parameters.keys():
        listbox.insert(END, param)
    listbox.grid(row=0, column=0, padx=5, pady=5)

    def confirm_delete():
        selected = listbox.curselection()
        for i in selected[::-1]:
            param = listbox.get(i)
            del parameters[param]
            del weights[param]
            del button_statuses[param]
            if param in active_case_load_weights:
                del active_case_load_weights[param]
        refresh_calculator_setup()
        popup.destroy()
        messagebox.showinfo("Success", "Rows deleted successfully!")

    Button(popup, text="Delete", command=confirm_delete).grid(row=1, column=0, pady=5)
    Button(popup, text="Cancel", command=lambda: popup.destroy()).grid(row=1, column=1, pady=5)

# Initialize the recent entries display
update_recent_entries()
update_active_case_load()

# Create the menu
create_menu(root)

# Function to mark a case as over
def mark_case_over(index):
    case = active_case_load[index]
    case_grade = case[2]
    result = messagebox.askyesno("Case Over", f"The current grade of the case is {case_grade:.2f}%. Did you win the case?")
    if result:
        messagebox.showinfo("Case Result", "You won the case.")
    else:
        messagebox.showinfo("Case Result", "You lost the case.")
    delete_active_case(index)

# Run the application
root.mainloop()

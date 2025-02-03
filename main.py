import tkinter as tk
from tkinter import ttk, messagebox
import csv
import json
import ast

# -------------------------------
# Load Diagnostic Data from JSON
# -------------------------------
try:
    with open("diagnosis.json", "r", encoding="utf-8") as json_file:
        diagnostics = json.load(json_file)
except FileNotFoundError:
    messagebox.showerror("Error", "diagnosis.json file not found.")
    diagnostics = {}  # Fallback to empty dictionary
except Exception as e:
    messagebox.showerror("Error", f"An error occurred loading diagnosis.json: {e}")
    diagnostics = {}


# -------------------------------
# Helper Function: Parse Range
# -------------------------------
def parse_range(range_value):
    """
    Convert the range value from the JSON (which may be a string like "(70, 105)")
    into a tuple of numbers (e.g., (70, 105)). If it's already a list or tuple,
    return it as a tuple.
    """
    if isinstance(range_value, (list, tuple)):
        return tuple(range_value)
    elif isinstance(range_value, str):
        try:
            parsed = ast.literal_eval(range_value)
            if isinstance(parsed, (list, tuple)):
                return tuple(parsed)
            else:
                return (None, None)
        except Exception:
            return (None, None)
    else:
        return (None, None)


# -------------------------------
# Tkinter GUI Setup
# -------------------------------
root = tk.Tk()
root.title("Blood Test Results")

# -------------------------------
# Patient Info Frame (Columns 1–6)
# -------------------------------
patient_info_frame = tk.LabelFrame(root, text="Patient Info", padx=10, pady=10)
patient_info_frame.pack(padx=10, pady=10, fill="x")

# Create labels for Patient Info
labels = ["Control No.", "Date", "Patient Name", "SEX", "Birthday", "AGE"]
for i, label in enumerate(labels):
    tk.Label(patient_info_frame, text=label + ":").grid(row=i, column=0, sticky="w")

# Create StringVar variables for patient info
control_no_var = tk.StringVar()
date_var = tk.StringVar()
patient_name_var = tk.StringVar()
sex_var = tk.StringVar()  # from CSV column 4 ("SEX")
birthday_var = tk.StringVar()
age_var = tk.StringVar()  # from CSV column 6 ("AGE")

# Create read-only entries for Patient Info
tk.Entry(patient_info_frame, textvariable=control_no_var, state="readonly").grid(row=0, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=date_var, state="readonly").grid(row=1, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=patient_name_var, state="readonly", width=28).grid(row=2, column=1,
                                                                                             sticky="w")
tk.Entry(patient_info_frame, textvariable=sex_var, state="readonly", width=5).grid(row=3, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=birthday_var, state="readonly").grid(row=4, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=age_var, state="readonly", width=5).grid(row=5, column=1, sticky="w")

# -------------------------------
# Treeview for Exam Results (Columns 7+)
# -------------------------------
tree = ttk.Treeview(root,
                    columns=("EXAMINTATION", "Conventional", "UNITS", "REFERENCE", "RESULT", "SI Units", "REFERENCE.1"),
                    show="headings")
tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

# Set up column headings and widths (adjust as needed)
cols = [("EXAMINTATION", 150), ("Conventional", 100), ("UNITS", 80),
        ("REFERENCE", 100), ("RESULT", 80), ("SI Units", 80), ("REFERENCE.1", 100)]
for col, width in cols:
    tree.heading(col, text=col)
    tree.column(col, width=width)

# -------------------------------
# Text Widget for Diagnosis Report
# -------------------------------
report_frame = tk.LabelFrame(root, text="Diagnosis Report", padx=10, pady=10)
report_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

report_text = tk.Text(report_frame, wrap="word", height=15)
report_text.pack(fill=tk.BOTH, expand=True)


# -------------------------------
# CSV Data Loading Function
# -------------------------------
def load_csv_data(file_path):
    """
    Load CSV data.
    The CSV is assumed to have patient info in the first 6 columns with headers:
       "Control No.", "Date:", "Patient Name:", "SEX", "Birthday", "AGE"
    and exam data in subsequent columns.
    """
    patient_info_set = False  # Only set patient info from the first row
    try:
        with open(file_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if not patient_info_set:
                    control_no_var.set(row.get("Control No.", ""))
                    date_var.set(row.get("Date:", ""))
                    patient_name_var.set(row.get("Patient Name:", ""))
                    sex_var.set(row.get("SEX", ""))  # Dynamic: pulled from CSV col 4
                    birthday_var.set(row.get("Birthday", ""))
                    age_val = row.get("AGE", "")
                    if age_val:
                        try:
                            age_int = int(float(age_val))
                            age_var.set(str(age_int))
                        except ValueError:
                            age_var.set(age_val)
                    else:
                        age_var.set("")
                    patient_info_set = True

                # Insert exam data row into the Treeview
                tree.insert("", "end", values=(
                    row.get("EXAMINTATION", ""),
                    row.get("Conventional", ""),
                    row.get("UNITS", ""),
                    row.get("REFERENCE", ""),
                    row.get("RESULT", ""),
                    row.get("SI Units", ""),
                    row.get("REFERENCE", "")
                ))
    except FileNotFoundError:
        messagebox.showerror("Error", f"File '{file_path}' not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


# -------------------------------
# Diagnostic Lookup Function
# -------------------------------
def get_diagnostic_result(exam, result, age, sex):
    """
    Look up diagnostic details for the given exam and test result.
    Uses the 'diagnostics' dictionary loaded from diagnosis.json.
    Returns a string report including:
       - Test result and reference values (based on age group and sex)
       - Conclusion
       - Medication and Dosage information
    If the test result is outside the defined range, an "Abnormal result" note is prepended.
    """
    exam = exam.strip()
    # Correct common misspellings (e.g., "Choesterol" to "Cholesterol")
    if exam.lower() in ["choesterol"]:
        exam = "Cholesterol"

    diag_info = diagnostics.get(exam)
    if not diag_info:
        return f"No diagnostic data available for exam: {exam}"

    try:
        # Use the "Conventional" value (assumed to start with a numeric value)
        value = float(result.split()[0])
    except Exception:
        return f"Invalid result value for {exam}: {result}"

    # Determine the age group based on the age value from CSV
    try:
        age_value = float(age)
    except ValueError:
        age_value = 0
    if 0 <= age_value <= 2:
        age_group = "Baby (0-2 years)"
    elif 3 <= age_value <= 12:
        age_group = "Child (3-12 years)"
    elif 20 <= age_value <= 35:
        age_group = "Young Adult (20-35 years)"
    elif 36 <= age_value <= 64:
        age_group = "Adult (36-64 years)"
    elif age_value >= 65:
        age_group = "Senior (65+ years)"
    else:
        age_group = "Unknown"

    def format_med_and_dosage(data):
        medications = data.get("Medication", [])
        med_str = ", ".join(medications) if medications else "N/A"
        dosage_data = data.get("Dosage", {})
        dosage_parts = []
        for key, val in dosage_data.items():
            dosage_parts.append(f"{key}: {val}")
        dosage_str = "; ".join(dosage_parts) if dosage_parts else "N/A"
        return med_str, dosage_str

    # For exams with multiple diagnostic categories (e.g., FBS)
    if exam == "FBS":
        for category in ["Normal", "Prediabetes"]:
            cat = diag_info.get(category)
            if not cat:
                continue
            r_min, r_max = parse_range(cat.get("Range", (None, None)))
            if r_min is not None and r_max is not None and r_min <= value <= r_max:
                age_ref = cat.get("Age", {}).get(age_group, "N/A")
                sex_ref = cat.get("Sex", {}).get(sex, "N/A")
                conclusion = cat.get("Conclusion", "")
                med_str, dosage_str = format_med_and_dosage(cat)
                return (f"Diagnosis for {exam} ({category}):\n"
                        f"Result: {value}\n"
                        f"Reference for {age_group}: {age_ref}\n"
                        f"Reference for {sex}: {sex_ref}\n\n"
                        f"{conclusion}\n"
                        f"Medication: {med_str}\n"
                        f"Dosage: {dosage_str}")
        # If none of the categories match the result, build a full report using the first available details.
        available_category = next(iter(diag_info.values()))
        r_min, r_max = parse_range(available_category.get("Range", (None, None)))
        age_ref = available_category.get("Age", {}).get(age_group, "N/A")
        sex_ref = available_category.get("Sex", {}).get(sex, "N/A")
        conclusion = available_category.get("Conclusion", "")
        med_str, dosage_str = format_med_and_dosage(available_category)
        diagnosis_text = (f"Diagnosis for {exam}:\n"
                          f"Result: {value}\n"
                          f"Reference for {age_group}: {age_ref}\n"
                          f"Reference for {sex}: {sex_ref}\n\n"
                          f"{conclusion}\n"
                          f"Medication: {med_str}\n"
                          f"Dosage: {dosage_str}")
        return f"Diagnosis for {exam}: Abnormal result ({value}).\n" + diagnosis_text

    else:
        # For exams with a single diagnostic range
        r_min, r_max = parse_range(diag_info.get("Range", (None, None)))
        age_ref = diag_info.get("Age", {}).get(age_group, "N/A")
        sex_ref = diag_info.get("Sex", {}).get(sex, "N/A")
        conclusion = diag_info.get("Conclusion", "Result is within the normal range.")
        med_str, dosage_str = format_med_and_dosage(diag_info)
        diagnosis_text = (f"Diagnosis for {exam}:\n"
                          f"Result: {value}\n"
                          f"Reference for {age_group}: {age_ref}\n"
                          f"Reference for {sex}: {sex_ref}\n\n"
                          f"{conclusion}\n"
                          f"Medication: {med_str}\n"
                          f"Dosage: {dosage_str}")
        # If the result is outside the defined range, prepend an abnormal note.
        if r_min is not None and r_max is not None and not (r_min <= value <= r_max):
            diagnosis_text = f"Diagnosis for {exam}: Abnormal result ({value}).\n" + diagnosis_text
        return diagnosis_text


# -------------------------------
# Generate Diagnosis Report Function
# -------------------------------
def generate_diagnosis_report():
    """
    Iterate through all exam rows in the Treeview using the "Conventional" value (column index 1)
    as the test result. Look up the diagnosis for each exam (using dynamic patient AGE and SEX)
    and output the full report into the Text widget.
    """
    report_text.delete("1.0", tk.END)  # Clear previous content

    patient_age = age_var.get()
    patient_sex = sex_var.get()
    overall_report = ""

    for item in tree.get_children():
        values = tree.item(item, "values")
        # We expect at least two columns: exam name (col0) and the conventional value (col1)
        if len(values) >= 2:
            exam = values[0]
            result = values[1]  # Conventional value as the test result
            diag_result = get_diagnostic_result(exam, result, patient_age, patient_sex)
            overall_report += diag_result + "\n" + ("-" * 50) + "\n"

    report_text.insert(tk.END, overall_report)


# -------------------------------
# Button to Generate Diagnosis Report
# -------------------------------
btn_report = tk.Button(root, text="Generate Diagnosis Report", command=generate_diagnosis_report)
btn_report.pack(pady=5)

# -------------------------------
# Load CSV Data (adjust the filename/path as needed)
# -------------------------------
load_csv_data("result_001.csv")

# Run the application
root.mainloop()

import tkinter as tk
from tkinter import ttk, messagebox
import csv
import json
import ast
from datetime import date

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
    Convert the range value (which may be a string like "(70, 105)" or a list)
    into a tuple of numbers.
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
# Helper Function: Format Medication and Dosage (for reports)
# -------------------------------
def format_med_and_dosage(data):
    med_data = data.get("Medication", "N/A")
    if isinstance(med_data, list):
        med_str = ", ".join(med_data) if med_data else "N/A"
    elif isinstance(med_data, str):
        med_str = med_data
    else:
        med_str = "N/A"
    dosage_data = data.get("Dosage", {})
    dosage_parts = []
    if isinstance(dosage_data, dict):
        for key, val in dosage_data.items():
            dosage_parts.append(f"{key}: {val}")
        dosage_str = "; ".join(dosage_parts) if dosage_parts else "N/A"
    else:
        dosage_str = str(dosage_data)
    return med_str, dosage_str

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

info_labels = ["Control No.", "Date", "Patient Name", "SEX", "Birthday", "AGE"]
for i, label in enumerate(info_labels):
    tk.Label(patient_info_frame, text=label + ":").grid(row=i, column=0, sticky="w")

control_no_var = tk.StringVar()
date_var = tk.StringVar()
patient_name_var = tk.StringVar()
sex_var = tk.StringVar()
birthday_var = tk.StringVar()
age_var = tk.StringVar()

tk.Entry(patient_info_frame, textvariable=control_no_var, state="readonly").grid(row=0, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=date_var, state="readonly").grid(row=1, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=patient_name_var, state="readonly", width=28).grid(row=2, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=sex_var, state="readonly", width=5).grid(row=3, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=birthday_var, state="readonly").grid(row=4, column=1, sticky="w")
tk.Entry(patient_info_frame, textvariable=age_var, state="readonly", width=5).grid(row=5, column=1, sticky="w")

# -------------------------------
# Treeview for Exam Results (7 Columns)
# -------------------------------
column_ids = ("EXAMINTATION", "Conventional", "UNITS", "REF_Con", "RESULT", "SI Units", "REF_SI")
tree = ttk.Treeview(root, columns=column_ids, show="headings")
tree.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

for col in column_ids:
    tree.heading(col, text=col)
    if col in ("EXAMINTATION", "REF_Con", "REF_SI"):
        tree.column(col, width=150)
    else:
        tree.column(col, width=100)

# -------------------------------
# Text Widget for Full Diagnosis Report
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
    Assumes patient info is in the first 6 columns and exam data in the next 7 columns.
    """
    patient_info_set = False
    try:
        with open(file_path, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            headers = [h.strip() for h in reader.fieldnames]
            print("CSV Headers:", headers)
            for row in reader:
                row = {k.strip(): (v.strip() if v is not None else "") for k, v in row.items()}
                if not patient_info_set:
                    control_no_var.set(row.get("Control No.", ""))
                    date_var.set(row.get("Date:", ""))
                    patient_name_var.set(row.get("Patient Name:", ""))
                    sex_var.set(row.get("SEX", ""))
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
                row_values = (
                    row.get("EXAMINTATION", ""),
                    row.get("Conventional", ""),
                    row.get("UNITS", ""),
                    row.get("REF_Con", ""),
                    row.get("RESULT", ""),
                    row.get("SI Units", ""),
                    row.get("REF_SI", "")
                )
                tree.insert("", "end", values=row_values)
    except FileNotFoundError:
        messagebox.showerror("Error", f"File '{file_path}' not found.")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# -------------------------------
# General Diagnostic Lookup Functions
# -------------------------------
def get_diagnostic_result(exam, result, age, sex):
    exam = exam.strip()
    if exam.lower() in ["choesterol"]:
        exam = "Cholesterol"
    diag_info = diagnostics.get(exam)
    if not diag_info:
        return f"No diagnostic data available for exam: {exam}"
    try:
        value = float(result.split()[0])
    except Exception:
        return f"Invalid result value for {exam}: {result}"
    try:
        age_value = float(age)
    except Exception:
        age_value = 0
    if 0 <= age_value <= 2:
        age_group = "Baby (0-2 years)"
    elif 3 <= age_value <= 12:
        age_group = "Child (3-12 years)"
    elif 13 <= age_value <= 19:
        age_group = "Teen (13-19 years)"
    elif 20 <= age_value <= 35:
        age_group = "Young Adult (20-35 years)"
    elif 36 <= age_value <= 64:
        age_group = "Adult (36-64 years)"
    elif age_value >= 65:
        age_group = "Senior (65+ years)"
    else:
        age_group = "Unknown"
    if "Range" in diag_info:
        r_min, r_max = parse_range(diag_info.get("Range", (None, None)))
        age_ref = diag_info.get("Age", {}).get(age_group, "N/A")
        sex_ref = diag_info.get("Sex", {}).get(sex, "N/A")
        conclusion = diag_info.get("Conclusion", "Result is within normal range.")
        med_str, dosage_str = format_med_and_dosage(diag_info)
        if r_min is not None and r_max is not None and not (r_min <= value <= r_max):
            diagnosis_text = f"Diagnosis for {exam}: Abnormal result ({value}).\n"
        else:
            diagnosis_text = f"Diagnosis for {exam}:\n"
        diagnosis_text += (f"Result: {value}\n"
                           f"Reference for {age_group}: {age_ref}\n"
                           f"Reference for {sex}: {sex_ref}\n\n"
                           f"{conclusion}\n"
                           f"Medication: {med_str}\n"
                           f"Dosage: {dosage_str}")
        return diagnosis_text
    else:
        for category, cat in diag_info.items():
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
        first_category = list(diag_info.values())[0]
        r_min, r_max = parse_range(first_category.get("Range", (None, None)))
        age_ref = first_category.get("Age", {}).get(age_group, "N/A")
        sex_ref = first_category.get("Sex", {}).get(sex, "N/A")
        conclusion = first_category.get("Conclusion", "")
        med_str, dosage_str = format_med_and_dosage(first_category)
        diagnosis_text = (f"Diagnosis for {exam}: Abnormal result ({value}).\n"
                          f"Result: {value}\n"
                          f"Reference for {age_group}: {age_ref}\n"
                          f"Reference for {sex}: {sex_ref}\n\n"
                          f"{conclusion}\n"
                          f"Medication: {med_str}\n"
                          f"Dosage: {dosage_str}")
        return diagnosis_text

def get_diagnostic_result_with_abnormal_flag(exam, result, age, sex):
    exam = exam.strip()
    if exam.lower() in ["choesterol"]:
        exam = "Cholesterol"
    diag_info = diagnostics.get(exam)
    if not diag_info:
        return (f"No diagnostic data available for exam: {exam}", False)
    try:
        value = float(result.split()[0])
    except Exception:
        return (f"Invalid result value for {exam}: {result}", False)
    try:
        age_value = float(age)
    except Exception:
        age_value = 0
    if 0 <= age_value <= 2:
        age_group = "Baby (0-2 years)"
    elif 3 <= age_value <= 12:
        age_group = "Child (3-12 years)"
    elif 13 <= age_value <= 19:
        age_group = "Teen (13-19 years)"
    elif 20 <= age_value <= 35:
        age_group = "Young Adult (20-35 years)"
    elif 36 <= age_value <= 64:
        age_group = "Adult (36-64 years)"
    elif age_value >= 65:
        age_group = "Senior (65+ years)"
    else:
        age_group = "Unknown"
    if "Range" in diag_info:
        r_min, r_max = parse_range(diag_info.get("Range", (None, None)))
        age_ref = diag_info.get("Age", {}).get(age_group, "N/A")
        sex_ref = diag_info.get("Sex", {}).get(sex, "N/A")
        conclusion = diag_info.get("Conclusion", "Result is within normal range.")
        med_str, dosage_str = format_med_and_dosage(diag_info)
        if r_min is not None and r_max is not None and not (r_min <= value <= r_max):
            diagnosis_text = f"Diagnosis for {exam}: Abnormal result ({value}).\n"
            abnormal = True
        else:
            diagnosis_text = f"Diagnosis for {exam}:\n"
            abnormal = False
        diagnosis_text += (f"Result: {value}\n"
                           f"Reference for {age_group}: {age_ref}\n"
                           f"Reference for {sex}: {sex_ref}\n\n"
                           f"{conclusion}\n"
                           f"Medication: {med_str}\n"
                           f"Dosage: {dosage_str}")
        return (diagnosis_text, abnormal)
    else:
        chosen_category = None
        abnormal = False
        for category, cat in diag_info.items():
            r_min, r_max = parse_range(cat.get("Range", (None, None)))
            if r_min is not None and r_max is not None and r_min <= value <= r_max:
                chosen_category = (category, cat)
                abnormal = (category.lower() != "normal")
                break
        if not chosen_category:
            first_category = list(diag_info.items())[0]
            category, cat = first_category
            chosen_category = (category, cat)
            abnormal = True
        category, cat = chosen_category
        age_ref = cat.get("Age", {}).get(age_group, "N/A")
        sex_ref = cat.get("Sex", {}).get(sex, "N/A")
        conclusion = cat.get("Conclusion", "")
        med_str, dosage_str = format_med_and_dosage(cat)
        diagnosis_text = (f"Diagnosis for {exam} ({category}):\n"
                          f"Result: {value}\n"
                          f"Reference for {age_group}: {age_ref}\n"
                          f"Reference for {sex}: {sex_ref}\n\n"
                          f"{conclusion}\n"
                          f"Medication: {med_str}\n"
                          f"Dosage: {dosage_str}")
        return (diagnosis_text, abnormal)

# -------------------------------
# Report Display Helper Function
# -------------------------------
def display_report_in_new_window(report_str, abnormal_count):
    title = f"Abnormal Diagnosis Report - {abnormal_count} Abnormal Result{'s' if abnormal_count != 1 else ''}"
    report_window = tk.Toplevel(root)
    report_window.title(title)
    text_widget = tk.Text(report_window, wrap="word", height=20, width=80)
    text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    header = f"{title}\n{'=' * len(title)}\n\n"
    text_widget.insert(tk.END, header + report_str)
    text_widget.config(state="disabled")

# -------------------------------
# Prescription Display Helper Function
# -------------------------------
def display_prescription_in_new_window(prescription_str):
    title = "Prescription - Rx"
    presc_window = tk.Toplevel(root)
    presc_window.title(title)
    text_widget = tk.Text(presc_window, wrap="word", height=20, width=80)
    text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    text_widget.insert(tk.END, prescription_str)
    text_widget.config(state="disabled")

# -------------------------------
# Generate Full Diagnosis Report Function
# -------------------------------
def generate_diagnosis_report():
    report_text.delete("1.0", tk.END)
    patient_age = age_var.get()
    patient_sex = sex_var.get()
    overall_report = ""
    for item in tree.get_children():
        values = tree.item(item, "values")
        if len(values) >= 2:
            exam = values[0]
            result = values[1]
            diag_result = get_diagnostic_result(exam, result, patient_age, patient_sex)
            overall_report += diag_result + "\n" + ("-" * 50) + "\n"
    report_text.insert(tk.END, overall_report)

# -------------------------------
# Generate Abnormal Diagnosis Report Function
# -------------------------------
def generate_abnormal_diagnosis_report():
    patient_age = age_var.get()
    patient_sex = sex_var.get()
    abnormal_report = ""
    abnormal_count = 0
    for item in tree.get_children():
        values = tree.item(item, "values")
        if len(values) >= 2:
            exam = values[0]
            result = values[1]
            diag_text, is_abnormal = get_diagnostic_result_with_abnormal_flag(exam, result, patient_age, patient_sex)
            if is_abnormal:
                abnormal_report += diag_text + "\n" + ("-" * 50) + "\n"
                abnormal_count += 1
    if abnormal_count > 0:
        display_report_in_new_window(abnormal_report, abnormal_count)
    else:
        messagebox.showinfo("Abnormal Diagnosis Report", "No abnormal results found.")

# -------------------------------
# Generate Prescription Function
# -------------------------------
def generate_prescription():
    """
    Generates a simplified prescription letter (Rx) that includes:
      - A letterhead with the current date and patient details.
      - For each abnormal exam with a valid medication recommendation,
        it displays only the medication name, dosage, and count (if count is not "0")
        in the format:
                [tab]Allopurinol Dosage: 100–300 mg daily 15x tablets
      - The final signature block is right aligned.
    """
    today_str = date.today().strftime("%B %d, %Y")
    patient_age = age_var.get()
    patient_sex = sex_var.get()
    patient_name = patient_name_var.get()
    try:
        age_val = float(age_var.get())
    except Exception:
        age_val = 0
    if 0 <= age_val <= 2:
        age_group = "Baby (0-2 years)"
    elif 3 <= age_val <= 12:
        age_group = "Child (3-12 years)"
    elif 13 <= age_val <= 19:
        age_group = "Teen (13-19 years)"
    elif 20 <= age_val <= 35:
        age_group = "Young Adult (20-35 years)"
    elif 36 <= age_val <= 64:
        age_group = "Adult (36-64 years)"
    elif age_val >= 65:
        age_group = "Senior (65+ years)"
    else:
        age_group = "Unknown"

    indent = "     "
    # Build letterhead as per sample.
    prescription = f"{indent}{'-' * 56}\n\n"
    prescription += f"{indent}Date: {today_str}\n"
    prescription += f"{indent}Name: {patient_name}\n"
    prescription += f"{indent}Age: {age_var.get()}    Sex: {patient_sex}\n"
    prescription += f"{indent}{'-' * 56}\n\n"
    prescription += f"{indent}Prescribed Medications:\n\n"
    prescription_found = False

    # Iterate over exam results.
    for item in tree.get_children():
        values = tree.item(item, "values")
        if len(values) >= 2:
            exam = values[0].strip()
            result = values[1]
            # Only include abnormal exams.
            _, is_abnormal = get_diagnostic_result_with_abnormal_flag(exam, result, age_var.get(), patient_sex)
            if is_abnormal:
                diag_info = diagnostics.get(exam, {})
                if not diag_info:
                    continue
                medication = diag_info.get("Medication", "").strip()
                if not medication or medication.lower() in ["none", "n/a", "no medication required"]:
                    continue
                if isinstance(medication, list):
                    medication = ", ".join(medication)
                dosage_info = diag_info.get("Dosage", {})
                if isinstance(dosage_info, dict):
                    dosage = dosage_info.get(age_group, "N/A")
                else:
                    dosage = dosage_info
                if dosage == "N/A":
                    continue
                count = diag_info.get("Count", "0")
                # Build the prescription line.
                if count != "0":
                    prescription += f"\t{medication} Dosage: {dosage} {count}x tablets\n\n"
                else:
                    prescription += f"\t{medication} Dosage: {dosage}\n\n"
                prescription_found = True

    if not prescription_found:
        prescription += f"{indent}No prescription required based on the current results.\n\n"

    # Add the signature block aligned to the right.
    prescription += "\n" + " " * 30 + "____________________________\n"
    prescription += " " * 30 + "   Physician/Practitioner\n"

    # Save file with a name based on Patient Name and Date.
    safe_name = patient_name.replace(" ", "_")
    safe_date = date.today().strftime("%B_%d_%Y")
    filename = f"{safe_name}_{safe_date}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(prescription)
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred while saving {filename}: {e}")

    display_prescription_in_new_window(prescription)

# -------------------------------
# Buttons
# -------------------------------
btn_report = tk.Button(root, text="Generate Diagnosis Report", command=generate_diagnosis_report)
btn_report.pack(pady=5)

btn_abnormal = tk.Button(root, text="Generate Abnormal Diagnosis Report", command=generate_abnormal_diagnosis_report)
btn_abnormal.pack(pady=5)

btn_prescribe = tk.Button(root, text="Prescribe", command=generate_prescription)
btn_prescribe.pack(pady=5)

# -------------------------------
# Load CSV Data (adjust the filename/path as needed)
# -------------------------------
load_csv_data("result_001.csv")

# Run the application
root.mainloop()

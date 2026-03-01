import streamlit as st

def format_json_errors(json_errors):
    msg = " JSON ERRORS FOUND \n\n"
    return msg + "\n".join(json_errors)

def format_csv_errors(csv_errors):
    msg = "CSV DATA ERRORS\n\n"
    has_error = False
    for error_type, rows in csv_errors.items():
        if rows:
            has_error = True
            name = error_type.replace("_", " ").title()
            msg += f"{name} → {rows}\n\n"
    return msg if has_error else None

def visualize_errors(csv_errors, json_errors):
    if json_errors:
        st.error(format_json_errors(json_errors))
    else:
        msg = format_csv_errors(csv_errors)
        if msg:
            st.warning(msg)
        else:
            print("No CSV errors found")
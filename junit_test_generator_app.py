import io
import zipfile
import re
from typing import List, Tuple

import requests
import streamlit as st


def parse_java_code(code: str) -> Tuple[List[str], List[str]]:
    """Extract class and method names from Java source code."""
    class_pattern = re.compile(r"\bclass\s+(\w+)")
    method_pattern = re.compile(r"\b(?:public|protected|private|static|final|synchronized|abstract|native|\s)+[\w<>\[\]]+\s+(\w+)\s*\(")
    classes = class_pattern.findall(code)
    methods = method_pattern.findall(code)
    return classes, methods


st.title("JUnit Test Generator")

st.write(
    "Upload Java source files or a ZIP archive containing Java files. "
    "The app will scan your code for classes and methods, send them to the "
    "backend API, and display the generated JUnit tests."
)

backend_url = st.text_input(
    "Backend API URL",
    value="http://localhost:8000/generate-tests",
    help="URL of the service that generates JUnit tests"
)

uploaded_files = st.file_uploader(
    "Upload .java files or a .zip archive",
    type=["java", "zip"],
    accept_multiple_files=True
)

java_sources = []
parsed_info = []

if uploaded_files:
    for uploaded in uploaded_files:
        filename = uploaded.name
        if filename.endswith(".zip"):
            with zipfile.ZipFile(uploaded) as zf:
                for name in zf.namelist():
                    if name.endswith(".java"):
                        code = zf.read(name).decode("utf-8", errors="ignore")
                        java_sources.append((name, code))
        else:
            code = uploaded.read().decode("utf-8", errors="ignore")
            java_sources.append((filename, code))

    for name, code in java_sources:
        classes, methods = parse_java_code(code)
        parsed_info.append({"file": name, "classes": classes, "methods": methods})

    st.subheader("Detected classes and methods")
    st.json(parsed_info)

if st.button("Generate JUnit Tests") and parsed_info:
    files_payload = [{"name": name, "content": code} for name, code in java_sources]
    try:
        response = requests.post(backend_url, json={"files": files_payload})
        if response.status_code == 200:
            st.success("Tests generated successfully.")
            st.download_button(
                label="Download tests as ZIP",
                data=response.content,
                file_name="junit-tests.zip",
                mime="application/zip"
            )
        else:
            st.error(f"Backend returned {response.status_code}: {response.text}")
    except Exception as exc:
        st.error(f"Failed to contact backend: {exc}")

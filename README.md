# 📄✨ Document Editor with AI-Powered Extraction

This is a full-stack web application designed to streamline document processing and data extraction. It allows users to upload various document types (PDF, DOCX, TXT), automatically extract key information using Google's Gemini AI, review and edit that data in a structured interface, and then save or export the refined information.

---

## 🚀 Features

* **Multi-Format Document Upload**: Supports PDF, DOCX, and TXT file uploads.
* **AI-Powered Data Extraction**: Leverages the Google Gemini API to intelligently extract key-value pairs from diverse document content (resumes, product labels, etc.).
* **Three-Column Interactive UI**:
    * **Live Document View**: Displays the document content, attempting to preserve basic formatting (bold, italic, font size) from PDFs.
    * **AI-Extracted Details**: Shows the raw, read-only data extracted by the AI.
    * **Editable Fields**: Allows users to modify the extracted data, with changes dynamically reflecting in the "Live Document View".
* **Document Save & Export**:
    * Save edited structured data and Quill delta content as JSON files.
    * Export the edited document as a new PDF file.
* **Clean & Responsive Design**: Built with React and Tailwind CSS for an intuitive user experience across devices.

---

## 🛠️ Technology Stack

**Backend (Python - Flask)**
* **Flask**: Web framework for handling API requests.
* **PyMuPDF (fitz)**: For efficient PDF text and basic formatting extraction.
* **python-docx**: For extracting text from DOCX files.
* **Google Generative AI (Gemini API)**: For AI-powered data extraction.
* **ReportLab**: For programmatic PDF generation from Quill delta content.
* **Flask-CORS**: Handles Cross-Origin Resource Sharing for frontend-backend communication.
* **Requests**: HTTP library for making API calls.

**Frontend (JavaScript - React)**
* **React.js**: For building the interactive single-page application UI.
* **Quill.js**: Used internally for handling rich text delta format and converting to HTML for display and PDF export.
* **Tailwind CSS**: Utility-first CSS framework for responsive and modern styling.

---

## ⚙️ Setup Instructions

Follow these steps to get the project up and running on your local machine.

### 1. Project Structure

Ensure you have the following directory structure:

```

document-editor/
├── backend/
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js
│   │   └── index.css
│   ├── package.json
│   ├── tailwind.config.js
│   └── postcss.config.js
└── README.md

````

### 2. Backend Setup (`backend/`)

1.  **Navigate to the `backend` folder**:
    ```bash
    cd document-editor/backend
    ```
2.  **Create `requirements.txt`**:
    ```
    Flask==2.3.2
    Flask-Cors==3.0.10
    PyMuPDF==1.23.8
    python-docx==1.1.0
    python-dotenv==1.0.1
    requests==2.31.0
    google-generativeai==0.3.0
    reportlab==4.1.0
    ```
3.  **Install Python dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Gemini API Key**:
    Open `app.py` and replace `"YOUR_GEMINI_API_KEY_HERE"` with your actual Google Gemini API key.
    ```python
    # Configure Gemini API
    API_KEY = "YOUR_GEMINI_API_KEY_HERE" # <--- PASTE YOUR GEMINI API KEY HERE
    genai.configure(api_key=API_KEY)
    ```
5.  **Run the Flask backend**:
    ```bash
    python app.py
    ```
    The backend will run on `http://localhost:5000`. Keep this terminal window open.

---

### 3. Frontend Setup (`frontend/`)

1.  **Navigate to the `frontend` folder** in a *new* terminal window:
    ```bash
    cd document-editor/frontend
    ```
2.  **Install Node.js dependencies**:
    ```bash
    npm install
    ```
3.  **Ensure Tailwind CSS Configuration**:
    Make sure `tailwind.config.js`, `postcss.config.js`, and `src/index.css` are configured as per standard Tailwind CSS setup for a React project.
4.  **Run the React frontend**:
    ```bash
    npm start
    ```
    The application should open in your browser, typically at `http://localhost:3000`. Keep this terminal window open.

---

## 🚀 How to Use

1.  **Ensure both backend and frontend are running** in separate terminal windows.
2.  **Open your browser** to `http://localhost:3000`.
3.  **Upload a Document**: Click "Choose File" to select a PDF, DOCX, or TXT file, then click "Upload & Extract".
4.  **View Extracted Data**:
    * **Live Document View (Column 1)**: See a representation of your document, with basic formatting.
    * **AI-Extracted Details (Column 2)**: View the structured data extracted by the Gemini AI.
    * **Edit Extracted Details (Column 3)**: Modify the extracted data. Changes here will dynamically update the "Live Document View".
5.  **Save Document**: Click "Save Document" to save the current edited data and document content as JSON files in the `backend/downloads` folder.
6.  **Export to PDF**: Click "Export to PDF" to generate a new PDF based on the content in the "Live Document View". This PDF will be saved to `backend/downloads` and automatically downloaded by your browser.

---

## 🚧 Future Enhancements

* **Improved Document Structure Preservation**: Currently, the PDF export maintains content, basic formatting (bold, italic, font size), but more complex layouts (multi-column, precise spacing) might not be perfectly replicated. This is an area for future improvement, potentially requiring more advanced PDF rendering techniques or a different approach to document representation.
* **Advanced AI Prompting**: Further refine the Gemini API prompts for more specialized or domain-specific extraction needs.
* **User Authentication**: Implement user login/registration if multi-user capabilities are desired.
* **Error Handling & UI Feedback**: Enhance user feedback for loading states, errors, and success messages.
* **Batch Processing**: Allow uploading and processing multiple documents at once.
* **Database Integration**: Store extracted and edited data in a persistent database (e.g., MongoDB, PostgreSQL) instead of just local JSON files.
````


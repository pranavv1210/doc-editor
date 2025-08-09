import React, { useState, useEffect, useRef, useCallback } from 'react';
import Quill from 'quill';
import 'quill/dist/quill.snow.css'; // Import Quill's CSS
import './index.css'; // Your Tailwind CSS imports are here

function App() {
  const quillViewerRef = useRef(null); // Ref for the read-only Quill viewer (Column 1)
  const quillInstanceRef = useRef(null); // To store Quill instance

  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [quillContentDelta, setQuillContentDelta] = useState([]); // Raw Quill delta from original doc
  const [extractedData, setExtractedData] = useState({}); // Read-only AI-extracted data
  const [editableData, setEditableData] = useState({}); // Editable AI-extracted data
  const [parsedDataOrder, setParsedDataOrder] = useState([]); // Order of fields from AI
  const [rawDocumentText, setRawDocumentText] = useState(""); // Raw text for Label Studio export
  const [labelStudioProjects, setLabelStudioProjects] = useState([]);
  const [labelStudioStatus, setLabelStudioStatus] = useState(null);
  const [projectIdToImport, setProjectIdToImport] = useState('');
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [projectTypeForLS, setProjectTypeForLS] = useState('generic'); // 'generic', 'resume', 'skills', 'education'
  const [message, setMessage] = useState('');

  // Initialize Quill viewer for Column 1
  useEffect(() => {
    // Initialize Quill only once
    if (quillViewerRef.current && !quillInstanceRef.current) {
      quillInstanceRef.current = new Quill(quillViewerRef.current, {
        theme: 'snow',
        readOnly: true, // Make it read-only
        modules: {
          toolbar: false // No toolbar for viewer
        }
      });
      quillInstanceRef.current.disable(); // Ensure it's not editable
    }

    // Update Quill's content whenever quillContentDelta changes
    const editor = quillInstanceRef.current;
    if (editor && quillContentDelta) {
        editor.setContents(quillContentDelta);
    }

    // Cleanup function: Destroy Quill instance when component unmounts
    // or when the ref changes (though ref should be stable for this use case)
    return () => {
      if (quillInstanceRef.current) {
        // Not strictly necessary to destroy, but good practice if the ref could change or component re-mounts often
        // However, for a single ref on the page, the instance typically persists for the component's lifetime.
        // The error is more likely from `setContents` interactions.
      }
    };
  }, [quillContentDelta]); // Keep quillContentDelta as a dependency to update content

  // Function to debounce state updates (useful for frequent input changes)
  const debounce = (func, delay) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  };

  // Reconstructs Quill delta from editableData for dynamic reflection in Column 1
  const updateQuillContentFromEditableData = useCallback(debounce((data) => {
    const newDelta = [];
    if (data && parsedDataOrder.length > 0) { // Ensure order is maintained
      parsedDataOrder.forEach(key => {
        const value = data[key];
        if (value !== undefined && value !== null) { // Only add if value exists
          let displayValue = value;
          // Attempt to pretty print JSON if it's a stringified object/array
          try {
            const parsed = JSON.parse(value);
            if (typeof parsed === 'object' && parsed !== null) {
              displayValue = JSON.stringify(parsed, null, 2);
            }
          } catch (e) {
            // Not a valid JSON string, use as is
          }

          newDelta.push({ insert: `${key.replace(/_/g, ' ').toUpperCase()}:\n`, attributes: { bold: true, size: 'large' } });
          newDelta.push({ insert: `${displayValue}\n\n` });
        }
      });
    } else if (data) { // Fallback if no specific order is available, just iterate keys
         Object.entries(data).forEach(([key, value]) => {
            if (value !== undefined && value !== null) {
                let displayValue = value;
                try {
                    const parsed = JSON.parse(value);
                    if (typeof parsed === 'object' && parsed !== null) {
                        displayValue = JSON.stringify(parsed, null, 2);
                    }
                } catch (e) {}

                newDelta.push({ insert: `${key.replace(/_/g, ' ').toUpperCase()}:\n`, attributes: { bold: true, size: 'large' } });
                newDelta.push({ insert: `${displayValue}\n\n` });
            }
         });
    }
    setQuillContentDelta(newDelta);
  }, 300), [parsedDataOrder, setQuillContentDelta]); // ADDED parsedDataOrder and setQuillContentDelta to dependencies

  // Effect to update Column 1 when editableData changes
  useEffect(() => {
    updateQuillContentFromEditableData(editableData);
  }, [editableData, updateQuillContentFromEditableData]);

  // Handle file selection
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setError(null);
    setMessage(null);
    setQuillContentDelta([]);
    setExtractedData({});
    setEditableData({});
    setParsedDataOrder([]);
    setRawDocumentText("");
  };

  // Handle file upload and initial parsing
  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first.');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await fetch('http://localhost:5000/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'File upload failed');
      }

      const data = await response.json();
      console.log("Upload response data:", data);

      setQuillContentDelta(data.quill_content_delta || []);
      setExtractedData(data.parsed_data || {});
      setEditableData(data.parsed_data || {}); // Initialize editable with extracted
      setParsedDataOrder(data.parsed_data_order || Object.keys(data.parsed_data || {}));
      setRawDocumentText(data.raw_text_content || "");

      setMessage('File processed and data extracted successfully!');

    } catch (err) {
      console.error('Upload Error:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle changes in editable fields (Column 3)
  const handleEditableChange = (field, value) => {
    setEditableData(prevData => ({
      ...prevData,
      [field]: value
    }));
  };

  // Handle saving the document
  const handleSave = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch('http://localhost:5000/save', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          edited_data: editableData,
          quill_content_delta: quillContentDelta, // Save the current state of the Quill view
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Save failed');
      }

      const data = await response.json();
      setMessage(data.message);
    } catch (err) {
      console.error('Save Error:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle exporting to PDF
  const handleExportPdf = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch('http://localhost:5000/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          quill_content_delta: quillContentDelta, // Export what's shown in Column 1
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'PDF export failed');
      }

      const data = await response.json();
      setMessage(data.message);
      if (data.pdf_download_url) {
        // Trigger client-side download
        window.open(`http://localhost:5000${data.pdf_download_url}`, '_blank');
      }
    } catch (err) {
      console.error('Export PDF Error:', err);
      setError(`Error: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Label Studio Integration functions
  const fetchLabelStudioStatus = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:5000/label-studio-status');
      const data = await response.json();
      setLabelStudioStatus(data);
    } catch (err) {
      console.error("Failed to fetch Label Studio status:", err);
      setLabelStudioStatus({ success: false, status: 'unknown_error', message: "Could not connect to backend for Label Studio status." });
    }
  }, []);

  const fetchLabelStudioProjects = useCallback(async () => {
    if (labelStudioStatus && labelStudioStatus.success) {
      try {
        const response = await fetch('http://localhost:5000/label-studio-projects');
        const data = await response.json();
        if (data.success) {
          setLabelStudioProjects(data.projects);
        } else {
          setError(`Failed to get LS projects: ${data.error}`);
        }
      } catch (err) {
        console.error("Failed to fetch Label Studio projects:", err);
        setError("Failed to fetch Label Studio projects.");
      }
    }
  }, [labelStudioStatus]);

  useEffect(() => {
    fetchLabelStudioStatus();
  }, [fetchLabelStudioStatus]);

  useEffect(() => {
    if (labelStudioStatus?.success) {
      fetchLabelStudioProjects();
    }
  }, [labelStudioStatus, fetchLabelStudioProjects]);

  const handleExportToLabelStudio = async () => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch('http://localhost:5000/export-to-label-studio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          parsed_data: editableData, // Send the currently editable data
          raw_document_text: rawDocumentText, // Send original raw text for annotation
          project_type: projectTypeForLS,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Export to Label Studio failed');
      }

      const data = await response.json();
      setMessage(data.message);
      setShowProjectModal(false); // Close modal on success
      fetchLabelStudioProjects(); // Refresh project list
      if (data.label_studio_url) {
        window.open(data.label_studio_url, '_blank');
      }
    } catch (err) {
      console.error('Export to LS Error:', err);
      setError(`Error exporting to Label Studio: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleImportFromLabelStudio = async () => {
    if (!projectIdToImport) {
      setError('Please enter a Project ID to import.');
      return;
    }

    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const response = await fetch('http://localhost:5000/import-from-label-studio', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ project_id: projectIdToImport }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'Import from Label Studio failed');
      }

      const data = await response.json();
      setMessage(data.message + (data.insights_file ? ` (Insights file: ${data.insights_file})` : ''));
      console.log('Annotated Data:', data.annotated_data);

      if (data.insights_download_url) {
        window.open(`http://localhost:5000${data.insights_download_url}`, '_blank');
      }

      // Optionally, you could update `editableData` with imported annotations
      // This would require mapping LS annotations back to your structured data format.
      // For now, we just log it.

    } catch (err) {
      console.error('Import from LS Error:', err);
      setError(`Error importing from Label Studio: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-4 font-sans text-gray-800">
      <h1 className="text-4xl font-bold text-center text-blue-700 mb-8 drop-shadow-md">
        Document Editor with AI-Powered Extraction 📄✨
      </h1>

      <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-lg p-6 mb-8">
        <div className="flex flex-col md:flex-row items-center justify-center gap-4 mb-6">
          <input
            type="file"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-500
              file:mr-4 file:py-2 file:px-4
              file:rounded-full file:border-0
              file:text-sm file:font-semibold
              file:bg-blue-50 file:text-blue-700
              hover:file:bg-blue-100 cursor-pointer"
          />
          <button
            onClick={handleUpload}
            disabled={!selectedFile || loading}
            className="w-full md:w-auto px-6 py-3 bg-blue-600 text-white rounded-lg
                       hover:bg-blue-700 transition-colors duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md"
          >
            {loading ? 'Processing...' : 'Upload & Extract'}
          </button>
        </div>

        <div className="flex flex-col md:flex-row items-center justify-center gap-4">
          <button
            onClick={handleSave}
            disabled={loading || Object.keys(editableData).length === 0}
            className="w-full md:w-auto px-6 py-3 bg-green-600 text-white rounded-lg
                       hover:bg-green-700 transition-colors duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md"
          >
            Save Document
          </button>
          <button
            onClick={handleExportPdf}
            disabled={loading || quillContentDelta.length === 0}
            className="w-full md:w-auto px-6 py-3 bg-purple-600 text-white rounded-lg
                       hover:bg-purple-700 transition-colors duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md"
          >
            Export to PDF
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-100 text-red-700 border border-red-300 rounded-md">
            {error}
          </div>
        )}
        {message && (
          <div className="mt-4 p-3 bg-green-100 text-green-700 border border-green-300 rounded-md">
            {message}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-7xl mx-auto">
        {/* Column 1: Live Input View Panel (Read-only Quill) */}
        <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Live Document View</h2>
          <div className="flex-grow">
            <div ref={quillViewerRef} className="ql-viewer">
              {/* Quill will render content here */}
              {quillContentDelta.length === 0 && (
                <p className="text-gray-500 text-center py-10">Upload a document (PDF, DOCX, TXT) to see its live view here. Edits in the third column will dynamically reflect here.</p>
              )}
            </div>
          </div>
        </div>

        {/* Column 2: AI Extracted Fields (Read-only) */}
        <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">AI-Extracted Details</h2>
          <div className="flex-grow space-y-4 overflow-y-auto max-h-[80vh] p-2 -m-2">
            {parsedDataOrder.length === 0 ? (
              <p className="text-gray-500 text-center py-10">Extracted details will appear here after document upload and processing.</p>
            ) : (
              parsedDataOrder.map(key => (
                extractedData[key] !== undefined && extractedData[key] !== null ? (
                  <div key={key} className="p-3 bg-gray-50 rounded-md border border-gray-200">
                    <h3 className="text-sm font-bold text-blue-600 mb-1">{key.replace(/_/g, ' ').toUpperCase()}:</h3>
                    <p className="text-gray-700 text-sm break-words whitespace-pre-wrap">{
                        typeof extractedData[key] === 'object' && extractedData[key] !== null
                        ? JSON.stringify(extractedData[key], null, 2)
                        : String(extractedData[key])
                    }</p>
                  </div>
                ) : null // Don't render if value is null or undefined
              ))
            )}
          </div>
        </div>

        {/* Column 3: Editable Fields */}
        <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Edit Extracted Details</h2>
          <div className="flex-grow space-y-4 overflow-y-auto max-h-[80vh] p-2 -m-2">
            {parsedDataOrder.length === 0 ? (
              <p className="text-gray-500 text-center py-10">Edit fields will appear here after AI extraction. Changes will reflect dynamically in the "Live View".</p>
            ) : (
              parsedDataOrder.map(key => (
                <div key={key}>
                  <label htmlFor={`edit-${key}`} className="block text-sm font-medium text-gray-700 mb-1">
                    {key.replace(/_/g, ' ').toUpperCase()}:
                  </label>
                  <textarea
                    id={`edit-${key}`}
                    value={editableData[key] || ''}
                    onChange={(e) => handleEditableChange(key, e.target.value)}
                    rows={Math.min(5, (String(editableData[key] || '')).split('\n').length + 1)}
                    className="editable-field"
                  />
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Label Studio Integration Section */}
      <div className="max-w-7xl mx-auto bg-white rounded-xl shadow-lg p-6 mt-8">
        <h2 className="text-xl font-semibold mb-4 text-gray-700">Label Studio Integration</h2>
        <p className="text-sm text-gray-600 mb-4">
          Status: {labelStudioStatus ? (
            labelStudioStatus.success ?
              <span className="text-green-600 font-medium">Connected ({labelStudioStatus.total_projects} projects)</span> :
              <span className="text-red-600 font-medium">Disconnected ({labelStudioStatus.status}: {labelStudioStatus.message})</span>
          ) : 'Checking...'}
        </p>
        
        {!labelStudioStatus?.success && labelStudioStatus?.setup_instructions && (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
            <p className="font-semibold text-yellow-800">Label Studio Setup Required:</p>
            <ul className="list-disc list-inside text-yellow-700 text-sm">
              {labelStudioStatus.setup_instructions.map((inst, idx) => (
                <li key={idx}>{inst}</li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-col md:flex-row gap-4 mb-4">
          <button
            onClick={() => setShowProjectModal(true)}
            disabled={loading || !labelStudioStatus?.success || Object.keys(editableData).length === 0}
            className="w-full md:w-auto px-6 py-3 bg-indigo-600 text-white rounded-lg
                       hover:bg-indigo-700 transition-colors duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md"
          >
            Export to Label Studio
          </button>
          
          <input
            type="text"
            placeholder="Enter Project ID to import"
            value={projectIdToImport}
            onChange={(e) => setProjectIdToImport(e.target.value)}
            className="editable-field flex-grow md:flex-grow-0"
            disabled={!labelStudioStatus?.success}
          />
          <button
            onClick={handleImportFromLabelStudio}
            disabled={loading || !labelStudioStatus?.success || !projectIdToImport}
            className="w-full md:w-auto px-6 py-3 bg-indigo-600 text-white rounded-lg
                       hover:bg-indigo-700 transition-colors duration-200
                       disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md"
          >
            Import from Label Studio
          </button>
        </div>

        {labelStudioProjects.length > 0 && labelStudioStatus?.success && (
          <div className="mt-4">
            <h3 className="text-lg font-semibold mb-2">Your Label Studio Projects:</h3>
            <ul className="list-disc list-inside text-gray-700">
              {labelStudioProjects.map(project => (
                <li key={project.id} className="mb-1 text-sm">
                  <strong>{project.title}</strong> (ID: {project.id}) - Tasks: {project.task_count}, Annotations: {project.annotation_count}
                  <a
                    href={`${labelStudioStatus.url}/projects/${project.id}/data`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-2 text-blue-500 hover:underline"
                  >
                    View
                  </a>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Export to Label Studio Modal */}
      {showProjectModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h2 className="text-xl font-semibold mb-4 text-gray-800">Export to Label Studio</h2>
            <div className="mb-4">
              <label htmlFor="projectType" className="block text-sm font-medium text-gray-700 mb-1">
                Project Type:
              </label>
              <select
                id="projectType"
                value={projectTypeForLS}
                onChange={(e) => setProjectTypeForLS(e.target.value)}
                className="editable-field"
              >
                <option value="generic">Generic Document Annotation</option>
                <option value="resume">Resume Annotation</option>
                <option value="skills">Skill Extraction</option>
                <option value="education">Education Validation</option>
              </select>
            </div>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowProjectModal(false)}
                className="px-4 py-2 bg-gray-300 text-gray-800 rounded-lg hover:bg-gray-400 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleExportToLabelStudio}
                disabled={loading}
                className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Exporting...' : 'Export'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;

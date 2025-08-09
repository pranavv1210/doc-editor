import React, { useState, useEffect, useRef, useCallback } from 'react';
import 'quill/dist/quill.snow.css'; // Still needed for basic ql-viewer styles
import './index.css'; // Your Tailwind CSS imports are here

function App() {
  const quillViewerRef = useRef(null); // This ref now points to a plain div

  const [selectedFile, setSelectedFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [quillContentDelta, setQuillContentDelta] = useState([]); // Raw Quill delta from original doc
  const [extractedData, setExtractedData] = useState({}); // Read-only AI-extracted data
  const [editableData, setEditableData] = useState({}); // Editable AI-extracted data
  const [parsedDataOrder, setParsedDataOrder] = useState([]); // Order of fields from AI
  const [message, setMessage] = useState('');
  const [viewerHtml, setViewerHtml] = useState(''); // State to store generated HTML for the viewer

  // Function to convert Quill Delta to simple HTML
  const convertDeltaToHtml = useCallback((delta) => {
    let html = '';
    if (!delta || !Array.isArray(delta)) {
      return '';
    }

    delta.forEach(op => {
      if (typeof op.insert === 'string') {
        let text = op.insert;
        let attributes = op.attributes || {};

        text = text.replace(/\n/g, '<br/>');

        let style = '';
        let tag = 'span';

        if (attributes.bold) style += 'font-weight: bold;';
        if (attributes.italic) style += 'font-style: italic;';
        if (attributes.size && typeof attributes.size === 'number') style += `font-size: ${attributes.size}px;`;
        if (attributes.font) style += `font-family: "${attributes.font}";`;

        if (op.insert.includes('\n') && op.insert.trim() === '') {
            html += '<br/>'; 
            return;
        } else if (op.insert.includes('\n')) {
            tag = 'div';
        }

        if (style) {
            html += `<${tag} style="${style}">${text}</${tag}>`;
        } else {
            html += `<${tag}>${text}</${tag}>`;
        }
      }
    });
    return html;
  }, []);

  // Effect: Convert quillContentDelta to HTML for the viewer
  useEffect(() => {
    setViewerHtml(convertDeltaToHtml(quillContentDelta));
  }, [quillContentDelta, convertDeltaToHtml]);


  // Function to debounce state updates (useful for frequent input changes)
  const debounce = (func, delay) => {
    let timeout;
    return (...args) => {
      clearTimeout(timeout);
      timeout = setTimeout(() => func.apply(this, args), delay);
    };
  };

  // Reconstructs Quill delta from editableData for dynamic reflection in Column 1
  const updateQuillContentLogic = useCallback(debounce((data) => {
    const newDelta = [];
    if (data && parsedDataOrder.length > 0) {
      parsedDataOrder.forEach(key => {
        const value = data[key];
        if (value !== undefined && value !== null) {
          let displayValue = value;
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
    } else if (data) {
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
  }, 300), [parsedDataOrder, setQuillContentDelta]);

  // Effect to trigger the debounced update when editableData changes
  useEffect(() => {
    updateQuillContentLogic(editableData);
  }, [editableData, updateQuillContentLogic]);


  // Handle file selection
  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
    setError(null);
    setMessage(null);
    setQuillContentDelta([]);
    setExtractedData({});
    setEditableData({});
    setParsedDataOrder([]);
    setViewerHtml('');
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
      setEditableData(data.parsed_data || {});
      setParsedDataOrder(data.parsed_data_order || Object.keys(data.parsed_data || {}));

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
          quill_content_delta: quillContentDelta,
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
          quill_content_delta: quillContentDelta,
        }),
      });

      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.error || 'PDF export failed');
      }

      const data = await response.json();
      setMessage(data.message);
      if (data.pdf_download_url) {
        window.open(`http://localhost:5000${data.pdf_download_url}`, '_blank');
      }
    } catch (err) {
      console.error('Export PDF Error:', err);
      setError(`Error: ${err.message}`);
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
        {/* Column 1: Live Input View Panel (Plain HTML from Quill Delta) */}
        <div className="bg-white p-6 rounded-xl shadow-lg flex flex-col">
          <h2 className="text-xl font-semibold mb-4 text-gray-700">Live Document View</h2>
          <div className="flex-grow">
            <div 
              ref={quillViewerRef} 
              className="p-4 border border-gray-200 rounded-md bg-gray-50 min-h-[500px] max-h-[80vh] overflow-y-auto" 
              dangerouslySetInnerHTML={{ __html: viewerHtml }}
            >
              {/* No children here */}
            </div>
            {quillContentDelta.length === 0 && !viewerHtml && (
                <p className="text-gray-500 text-center py-10 mt-4">Upload a document (PDF, DOCX, TXT) to see its live view here. Edits in the third column will dynamically reflect here.</p>
            )}
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
                ) : null
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
    </div>
  );
}

export default App;

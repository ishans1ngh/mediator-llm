import { useState } from 'react';

export default function MRIUploader({ patientId, onAnalysisComplete }) {
  const [t1File, setT1File] = useState(null);
  const [t1ceFile, setT1ceFile] = useState(null);
  const [t2File, setT2File] = useState(null);
  const [flairFile, setFlairFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [fileId, setFileId] = useState(null);
  const [error, setError] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  const handleFileChange = (setter) => (e) => {
    const file = e.target.files[0];
    if (file) {
      if (!file.name.endsWith('.nii') && !file.name.endsWith('.nii.gz')) {
        setError('Only .nii or .nii.gz files are supported');
        return;
      }
      setter(file);
      setError(null);
    }
  };

  const handleUpload = async () => {
    if (!t1File || !t1ceFile || !t2File || !flairFile) {
      setError('All four MRI modalities are required (T1, T1ce, T2, FLAIR)');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('t1', t1File);
      formData.append('t1ce', t1ceFile);
      formData.append('t2', t2File);
      formData.append('flair', flairFile);

      const response = await fetch('http://127.0.0.1:8000/api/mri/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setFileId(data.file_id);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!fileId) {
      setError('No uploaded file to analyze');
      return;
    }

    setAnalyzing(true);
    setError(null);

    try {
      const response = await fetch(`http://127.0.0.1:8000/api/mri/analyze?file_id=${fileId}`, {
        method: 'POST',
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      const data = await response.json();
      setAnalysisResult(data);
      onAnalysisComplete(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className='max-w-4xl mx-auto px-6 py-6'>
      <div className='bg-white rounded-lg border border-slate-200 p-6'>
        <h2 className='text-lg font-semibold text-slate-900 mb-4'>MRI Upload</h2>
        <p className='text-sm text-slate-600 mb-6'>
          Upload all four MRI modalities required for BraTS segmentation analysis.
          Supported formats: .nii, .nii.gz
        </p>

        <div className='space-y-4'>
          <div>
            <label className='block text-sm font-medium text-slate-700 mb-1'>T1 (Native T1-weighted)</label>
            <input
              type='file'
              accept='.nii,.nii.gz'
              onChange={handleFileChange(setT1File)}
              className='w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            />
            {t1File && <p className='text-xs text-slate-500 mt-1'>{t1File.name}</p>}
          </div>

          <div>
            <label className='block text-sm font-medium text-slate-700 mb-1'>T1ce (T1-weighted contrast-enhanced)</label>
            <input
              type='file'
              accept='.nii,.nii.gz'
              onChange={handleFileChange(setT1ceFile)}
              className='w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            />
            {t1ceFile && <p className='text-xs text-slate-500 mt-1'>{t1ceFile.name}</p>}
          </div>

          <div>
            <label className='block text-sm font-medium text-slate-700 mb-1'>T2 (T2-weighted)</label>
            <input
              type='file'
              accept='.nii,.nii.gz'
              onChange={handleFileChange(setT2File)}
              className='w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            />
            {t2File && <p className='text-xs text-slate-500 mt-1'>{t2File.name}</p>}
          </div>

          <div>
            <label className='block text-sm font-medium text-slate-700 mb-1'>FLAIR (Fluid-attenuated inversion recovery)</label>
            <input
              type='file'
              accept='.nii,.nii.gz'
              onChange={handleFileChange(setFlairFile)}
              className='w-full text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100'
            />
            {flairFile && <p className='text-xs text-slate-500 mt-1'>{flairFile.name}</p>}
          </div>
        </div>

        <div className='mt-6 flex gap-3'>
          {!fileId ? (
            <button
              onClick={handleUpload}
              disabled={uploading}
              className='flex-1 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 text-sm font-medium'
            >
              {uploading ? 'Uploading...' : 'Upload MRI Files'}
            </button>
          ) : (
            <button
              onClick={handleAnalyze}
              disabled={analyzing}
              className='flex-1 py-2.5 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-green-300 text-sm font-medium'
            >
              {analyzing ? 'Analyzing...' : 'Analyze MRI'}
            </button>
          )}
        </div>

        {error && (
          <div className='mt-4 bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3'>
            {error}
          </div>
        )}

        {analysisResult && (
          <div className='mt-4 bg-slate-50 border border-slate-200 rounded-lg p-4'>
            <h3 className='text-sm font-semibold text-slate-900 mb-2'>Analysis Result</h3>
            <div className='text-xs text-slate-600 space-y-1'>
              <p><strong>Status:</strong> {analysisResult.segmentation?.status}</p>
              {analysisResult.segmentation?.segmentation_available && (
                <>
                  <p><strong>Tumor Detected:</strong> {analysisResult.segmentation.tumor_detected ? 'Yes' : 'No'}</p>
                  {analysisResult.segmentation.total_tumor_voxels !== undefined && (
                    <p><strong>Total Tumor Voxels:</strong> {analysisResult.segmentation.total_tumor_voxels}</p>
                  )}
                </>
              )}
              {analysisResult.segmentation?.error && (
                <p className='text-red-600'><strong>Error:</strong> {analysisResult.segmentation.error}</p>
              )}
              <p className='text-slate-400 italic mt-2'>{analysisResult.segmentation?.medical_disclaimer}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

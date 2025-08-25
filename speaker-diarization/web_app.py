#!/usr/bin/env python3
"""
Simple web interface for speaker diarization pipeline
Provides upload, processing, and transcript viewing capabilities
"""

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
import threading
import queue
import time
from pathlib import Path
from datetime import datetime
import sys

# Import our transcription module
from transcribe_with_speakers import SpeakerDiarizer

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'output'

# Ensure directories exist
Path(app.config['UPLOAD_FOLDER']).mkdir(exist_ok=True)
Path(app.config['OUTPUT_FOLDER']).mkdir(exist_ok=True)

# Global storage for processing status
processing_status = {}
processing_lock = threading.Lock()

# Allowed audio extensions
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'opus', 'webm'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

class ProcessingThread(threading.Thread):
    """Background thread for audio processing"""
    
    def __init__(self, file_path, job_id, whisper_model='base', num_speakers=2):
        super().__init__()
        self.file_path = file_path
        self.job_id = job_id
        self.whisper_model = whisper_model
        self.num_speakers = num_speakers
        self.daemon = True
        
    def run(self):
        """Run the transcription process"""
        global processing_status
        
        try:
            # Update status
            with processing_lock:
                processing_status[self.job_id] = {
                    'status': 'processing',
                    'progress': 10,
                    'message': 'Initializing...',
                    'start_time': datetime.now().isoformat()
                }
            
            # Initialize diarizer
            hf_token = os.environ.get('HF_TOKEN')
            if not hf_token:
                with processing_lock:
                    processing_status[self.job_id]['message'] = 'Warning: No HF_TOKEN, speaker diarization disabled'
            
            diarizer = SpeakerDiarizer(hf_token=hf_token)
            
            # Update progress
            with processing_lock:
                processing_status[self.job_id]['progress'] = 30
                processing_status[self.job_id]['message'] = 'Loading audio file...'
            
            # Process audio
            result = diarizer.transcribe_with_speakers(
                self.file_path,
                whisper_model=self.whisper_model,
                num_speakers=self.num_speakers,
                batch_size=8
            )
            
            # Update progress
            with processing_lock:
                processing_status[self.job_id]['progress'] = 80
                processing_status[self.job_id]['message'] = 'Saving results...'
            
            # Save outputs
            base_name = Path(self.file_path).stem
            output_base = f"{self.job_id}_{base_name}"
            diarizer.save_outputs(result, output_base, app.config['OUTPUT_FOLDER'])
            
            # Update final status
            with processing_lock:
                processing_status[self.job_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Processing complete!',
                    'output_files': {
                        'text': f"{output_base}.txt",
                        'json': f"{output_base}.json",
                        'srt': f"{output_base}.srt"
                    },
                    'segments': len(result.get('segments', [])),
                    'end_time': datetime.now().isoformat()
                }
                
        except Exception as e:
            # Handle errors
            with processing_lock:
                processing_status[self.job_id] = {
                    'status': 'error',
                    'progress': 0,
                    'message': f'Error: {str(e)}',
                    'end_time': datetime.now().isoformat()
                }

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and start processing"""
    
    if 'audio' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    # Save uploaded file
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    job_id = f"{timestamp}_{Path(filename).stem}"
    
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{job_id}_{filename}")
    file.save(file_path)
    
    # Get processing parameters
    whisper_model = request.form.get('model', 'base')
    num_speakers = int(request.form.get('speakers', 2))
    
    # Start processing in background
    processor = ProcessingThread(file_path, job_id, whisper_model, num_speakers)
    processor.start()
    
    return jsonify({
        'job_id': job_id,
        'message': 'Processing started',
        'filename': filename
    })

@app.route('/status/<job_id>')
def get_status(job_id):
    """Get processing status"""
    with processing_lock:
        if job_id in processing_status:
            return jsonify(processing_status[job_id])
        else:
            return jsonify({'error': 'Job not found'}), 404

@app.route('/transcript/<job_id>')
def get_transcript(job_id):
    """Get transcript content"""
    with processing_lock:
        if job_id not in processing_status:
            return jsonify({'error': 'Job not found'}), 404
        
        status = processing_status[job_id]
        if status['status'] != 'completed':
            return jsonify({'error': 'Processing not complete'}), 400
        
        # Read transcript file
        txt_file = os.path.join(app.config['OUTPUT_FOLDER'], status['output_files']['text'])
        if not os.path.exists(txt_file):
            return jsonify({'error': 'Transcript file not found'}), 404
        
        with open(txt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return jsonify({
            'content': content,
            'filename': status['output_files']['text']
        })

@app.route('/download/<job_id>/<file_type>')
def download_file(job_id, file_type):
    """Download output file"""
    with processing_lock:
        if job_id not in processing_status:
            return jsonify({'error': 'Job not found'}), 404
        
        status = processing_status[job_id]
        if status['status'] != 'completed':
            return jsonify({'error': 'Processing not complete'}), 400
        
        if file_type not in ['text', 'json', 'srt']:
            return jsonify({'error': 'Invalid file type'}), 400
        
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], status['output_files'][file_type])
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)

@app.route('/jobs')
def list_jobs():
    """List all processing jobs"""
    with processing_lock:
        jobs = []
        for job_id, status in processing_status.items():
            jobs.append({
                'id': job_id,
                'status': status['status'],
                'message': status.get('message', ''),
                'progress': status.get('progress', 0)
            })
        return jsonify(jobs)

if __name__ == '__main__':
    print("=" * 60)
    print("SPEAKER DIARIZATION WEB INTERFACE")
    print("=" * 60)
    print()
    
    # Check for HF_TOKEN
    if not os.environ.get('HF_TOKEN'):
        print("⚠️  Warning: HF_TOKEN not set")
        print("   Speaker diarization will not work without it.")
        print("   Set it with: export HF_TOKEN='your_token_here'")
        print()
    
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()
    
    app.run(debug=False, host='0.0.0.0', port=5000)
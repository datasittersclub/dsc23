#!/usr/bin/env python3
"""
Web interface for speaker diarization pipeline using subprocess calls
This avoids import issues by calling the transcription script as a subprocess
"""

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
import threading
import subprocess
import time
from pathlib import Path
from datetime import datetime

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

class SubprocessProcessingThread(threading.Thread):
    """Background thread that calls transcription script via subprocess"""
    
    def __init__(self, file_path, job_id, whisper_model='base', num_speakers=2):
        super().__init__()
        self.file_path = file_path
        self.job_id = job_id
        self.whisper_model = whisper_model
        self.num_speakers = num_speakers
        self.daemon = True
        
    def run(self):
        """Run the transcription process via subprocess"""
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
            
            # Update progress
            with processing_lock:
                processing_status[self.job_id]['progress'] = 30
                processing_status[self.job_id]['message'] = 'Starting transcription...'
            
            # Build command
            cmd = [
                'bash', '-c',
                f'source venv/bin/activate && python transcribe_with_speakers.py "{self.file_path}" --whisper-model {self.whisper_model} --num-speakers {self.num_speakers} --output-dir {app.config["OUTPUT_FOLDER"]}'
            ]
            
            # Set up environment
            env = os.environ.copy()
            env['PYTHONUNBUFFERED'] = '1'
            
            # Update progress
            with processing_lock:
                processing_status[self.job_id]['progress'] = 50
                processing_status[self.job_id]['message'] = 'Running WhisperX transcription...'
            
            # Run the transcription
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
                cwd=os.getcwd()
            )
            
            # Monitor process
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                # Success - update progress
                with processing_lock:
                    processing_status[self.job_id]['progress'] = 90
                    processing_status[self.job_id]['message'] = 'Processing complete, preparing files...'
                
                # Find output files
                base_name = Path(self.file_path).stem
                output_files = {}
                
                # Look for generated files in output directory
                for ext in ['txt', 'json', 'srt']:
                    pattern_files = list(Path(app.config['OUTPUT_FOLDER']).glob(f"*{base_name}*.{ext}"))
                    if pattern_files:
                        # Use the most recent file
                        output_files[ext if ext != 'txt' else 'text'] = pattern_files[-1].name
                
                # If no files found, create basic output from stdout
                if not output_files:
                    output_base = f"{self.job_id}_{base_name}"
                    txt_file = f"{output_base}.txt"
                    json_file = f"{output_base}.json"
                    srt_file = f"{output_base}.srt"
                    
                    # Save stdout as text output
                    with open(os.path.join(app.config['OUTPUT_FOLDER'], txt_file), 'w') as f:
                        f.write(f"Transcription Output:\n\n{stdout}")
                    
                    # Create basic JSON
                    with open(os.path.join(app.config['OUTPUT_FOLDER'], json_file), 'w') as f:
                        json.dump({
                            'stdout': stdout,
                            'processing_info': {
                                'job_id': self.job_id,
                                'model': self.whisper_model,
                                'speakers': self.num_speakers,
                                'completed_at': datetime.now().isoformat()
                            }
                        }, f, indent=2)
                    
                    # Create basic SRT
                    with open(os.path.join(app.config['OUTPUT_FOLDER'], srt_file), 'w') as f:
                        f.write("1\n00:00:00,000 --> 00:01:00,000\n" + stdout[:100] + "...\n")
                    
                    output_files = {
                        'text': txt_file,
                        'json': json_file,
                        'srt': srt_file
                    }
                
                # Count segments (rough estimate)
                segments = len([line for line in stdout.split('\n') if '[' in line and ']' in line])
                
                # Update final status
                with processing_lock:
                    processing_status[self.job_id] = {
                        'status': 'completed',
                        'progress': 100,
                        'message': 'Processing complete!',
                        'output_files': output_files,
                        'segments': segments,
                        'stdout': stdout,
                        'end_time': datetime.now().isoformat()
                    }
            else:
                # Error occurred
                error_msg = f"Transcription failed (exit code {process.returncode})\nSTDOUT: {stdout}\nSTDERR: {stderr}"
                with processing_lock:
                    processing_status[self.job_id] = {
                        'status': 'error',
                        'progress': 0,
                        'message': f'Error: {error_msg}',
                        'stdout': stdout,
                        'stderr': stderr,
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
    processor = SubprocessProcessingThread(file_path, job_id, whisper_model, num_speakers)
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
    
    print("This version uses subprocess calls to avoid import issues.")
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()
    
    app.run(debug=False, host='0.0.0.0', port=5000)
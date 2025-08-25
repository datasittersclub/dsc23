#!/usr/bin/env python3
"""
Demo version of web interface for speaker diarization pipeline
This version simulates the processing for demonstration purposes
"""

from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import json
import threading
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

class DemoProcessingThread(threading.Thread):
    """Demo background thread that simulates audio processing"""
    
    def __init__(self, file_path, job_id, whisper_model='base', num_speakers=2):
        super().__init__()
        self.file_path = file_path
        self.job_id = job_id
        self.whisper_model = whisper_model
        self.num_speakers = num_speakers
        self.daemon = True
        
    def run(self):
        """Simulate the transcription process"""
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
            
            # Simulate initialization
            time.sleep(2)
            with processing_lock:
                processing_status[self.job_id]['progress'] = 30
                processing_status[self.job_id]['message'] = 'Loading audio file...'
            
            # Simulate transcription
            time.sleep(3)
            with processing_lock:
                processing_status[self.job_id]['progress'] = 60
                processing_status[self.job_id]['message'] = 'Transcribing with Whisper...'
            
            # Simulate diarization
            time.sleep(3)
            with processing_lock:
                processing_status[self.job_id]['progress'] = 80
                processing_status[self.job_id]['message'] = 'Identifying speakers...'
            
            # Simulate saving
            time.sleep(1)
            with processing_lock:
                processing_status[self.job_id]['progress'] = 90
                processing_status[self.job_id]['message'] = 'Saving results...'
            
            # Create demo output files
            base_name = Path(self.file_path).stem
            output_base = f"{self.job_id}_{base_name}"
            
            # Create demo transcript
            demo_transcript = f"""Demo Transcript - {base_name}
Processing completed with model: {self.whisper_model}
Speakers detected: {self.num_speakers}

[00:00 - 00:05] SPEAKER_01: This is a demonstration of the speaker diarization pipeline.

[00:05 - 00:08] SPEAKER_02: The system would normally identify who is speaking when.

[00:08 - 00:12] SPEAKER_01: In this demo, we're showing how the web interface works.

[00:12 - 00:15] SPEAKER_02: The actual processing would use WhisperX and PyAnnote for real transcription.

Processing completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
File: {self.file_path}
Model: {self.whisper_model}
Speakers: {self.num_speakers}
"""
            
            # Save demo files
            txt_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_base}.txt")
            json_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_base}.json")
            srt_file = os.path.join(app.config['OUTPUT_FOLDER'], f"{output_base}.srt")
            
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(demo_transcript)
            
            demo_json = {
                "segments": [
                    {"start": 0.0, "end": 5.0, "speaker": "SPEAKER_01", "text": "This is a demonstration of the speaker diarization pipeline."},
                    {"start": 5.0, "end": 8.0, "speaker": "SPEAKER_02", "text": "The system would normally identify who is speaking when."},
                    {"start": 8.0, "end": 12.0, "speaker": "SPEAKER_01", "text": "In this demo, we're showing how the web interface works."},
                    {"start": 12.0, "end": 15.0, "speaker": "SPEAKER_02", "text": "The actual processing would use WhisperX and PyAnnote for real transcription."}
                ],
                "metadata": {
                    "processing_date": datetime.now().isoformat(),
                    "whisper_model": self.whisper_model,
                    "num_speakers": self.num_speakers,
                    "file": self.file_path
                }
            }
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(demo_json, f, indent=2)
            
            demo_srt = """1
00:00:00,000 --> 00:00:05,000
SPEAKER_01: This is a demonstration of the speaker diarization pipeline.

2
00:00:05,000 --> 00:00:08,000
SPEAKER_02: The system would normally identify who is speaking when.

3
00:00:08,000 --> 00:00:12,000
SPEAKER_01: In this demo, we're showing how the web interface works.

4
00:00:12,000 --> 00:00:15,000
SPEAKER_02: The actual processing would use WhisperX and PyAnnote for real transcription.
"""
            
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(demo_srt)
            
            # Update final status
            with processing_lock:
                processing_status[self.job_id] = {
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Processing complete! (Demo mode)',
                    'output_files': {
                        'text': f"{output_base}.txt",
                        'json': f"{output_base}.json",
                        'srt': f"{output_base}.srt"
                    },
                    'segments': 4,
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
    processor = DemoProcessingThread(file_path, job_id, whisper_model, num_speakers)
    processor.start()
    
    return jsonify({
        'job_id': job_id,
        'message': 'Processing started (Demo mode)',
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
    print("SPEAKER DIARIZATION WEB INTERFACE - DEMO MODE")
    print("=" * 60)
    print()
    print("⚠️  This is a DEMO version that simulates processing.")
    print("   For real transcription, use the full web_app.py with")
    print("   proper environment setup (conda/venv with all dependencies).")
    print()
    print("Starting server at http://localhost:5000")
    print("Press Ctrl+C to stop")
    print()
    
    app.run(debug=False, host='0.0.0.0', port=5000)
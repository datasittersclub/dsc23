from flask import Flask, request, render_template, jsonify, redirect, url_for
import requests
from modules.llm_provider import LLMProvider
from modules.story_processor import SimpleStoryProcessor
from modules.corpus_manager import process_entire_corpus
from modules.visualization import prepare_visualization_data, export_for_html_visualization
import os

app = Flask(__name__)

# List available models from Ollama endpoint
@app.route('/ollama_models')
def ollama_models():
    ollama_url = request.args.get('url', OLLAMA_CONFIG['url'])
    try:
        resp = requests.get(f'{ollama_url}/api/tags', timeout=5)
        if resp.status_code == 200:
            try:
                tags = resp.json().get('models', [])
                models = [m['name'] for m in tags]
                # Filter by enabled models if configured
                enabled_models = OLLAMA_CONFIG.get('enabled_models', {})
                if enabled_models:
                    models = [m for m in models if enabled_models.get(m, True)]
                return jsonify(models)
            except ValueError:
                return jsonify({'error': 'Invalid JSON response from Ollama', 'fallback_models': ['llama2', 'mistral', 'codellama']})
        else:
            return jsonify({'error': f'HTTP {resp.status_code}', 'fallback_models': ['llama2', 'mistral', 'codellama']})
    except requests.exceptions.ConnectTimeout:
        return jsonify({'error': 'Connection timeout', 'fallback_models': ['llama2', 'mistral', 'codellama']})
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Connection refused', 'fallback_models': ['llama2', 'mistral', 'codellama']})
    except Exception as e:
        return jsonify({'error': str(e), 'fallback_models': ['llama2', 'mistral', 'codellama']})

# Test Ollama connection
@app.route('/test_ollama')
def test_ollama():
    ollama_url = request.args.get('url', OLLAMA_CONFIG['url'])
    try:
        resp = requests.get(f'{ollama_url}/api/tags', timeout=5)
        if resp.status_code == 200:
            try:
                data = resp.json()
                return jsonify({'success': True, 'models_count': len(data.get('models', []))})
            except ValueError:
                return jsonify({'success': False, 'error': f'Invalid JSON response. Got HTML instead. Response: {resp.text[:200]}...'})
        else:
            return jsonify({'success': False, 'error': f'HTTP {resp.status_code}: {resp.text[:200]}'})
    except requests.exceptions.ConnectTimeout:
        return jsonify({'success': False, 'error': 'Connection timeout. Is Ollama running?'})
    except requests.exceptions.ConnectionError:
        return jsonify({'success': False, 'error': 'Connection refused. Check if Ollama is running and URL is correct.'})
    except Exception as e:
        return jsonify({'success': False, 'error': f'Unexpected error: {str(e)}'})
# List available results (JSON files)
@app.route('/list_results')
def list_results():
    results_dir = os.getcwd()
    files = [f for f in os.listdir(results_dir) if f.endswith('_visualization.json')]
    return jsonify(files)

# Preview a result file
@app.route('/preview_result')
def preview_result():
    name = request.args.get('name')
    if not name:
        return jsonify({'error': 'No result specified'}), 400
    path = os.path.join(os.getcwd(), name)
    if not os.path.exists(path):
        return jsonify({'error': 'File not found'}), 404
    from flask import Flask, request, render_template, jsonify, redirect, url_for
    import requests
    from modules.llm_provider import LLMProvider
    from modules.story_processor import SimpleStoryProcessor
    from modules.corpus_manager import process_entire_corpus
    from modules.visualization import prepare_visualization_data, export_for_html_visualization
    import os

    app = Flask(__name__)

    # List available models from Ollama endpoint
    with open(path, 'r', encoding='utf-8') as f:
        data = f.read()
    try:
        import json
        return jsonify(json.loads(data))
    except Exception:
        return jsonify({'error': 'Invalid JSON'})

app = Flask(__name__)

API_KEYS = {}
OLLAMA_CONFIG = {'url': 'http://localhost:11434', 'enabled_models': {}}
CORPUS_DIR = os.path.join(os.getcwd(), 'corpus_uploads')
os.makedirs(CORPUS_DIR, exist_ok=True)

# List corpus folders in web directory and uploads
def get_corpus_folders():
    candidates = []
    # Only list folders inside corpus_uploads
    if os.path.exists(CORPUS_DIR):
        for name in os.listdir(CORPUS_DIR):
            path = os.path.join(CORPUS_DIR, name)
            if os.path.isdir(path) and not name.startswith('.'):
                candidates.append(name)  # Just the folder name, not the full path
    return candidates

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api_keys', methods=['GET', 'POST'])
def api_keys():
    if request.method == 'POST':
        provider = request.form['provider']
        key = request.form['key']
        API_KEYS[provider] = key
        return redirect(url_for('api_keys'))
    return render_template('api_keys.html', api_keys=API_KEYS, ollama_config=OLLAMA_CONFIG)

# Save Ollama configuration
@app.route('/save_ollama_config', methods=['POST'])
def save_ollama_config():
    OLLAMA_CONFIG['url'] = request.form.get('ollama_url', 'http://localhost:11434')
    enabled_models = request.form.getlist('enabled_models')
    # Update enabled models
    for model in enabled_models:
        OLLAMA_CONFIG['enabled_models'][model] = True
    return redirect(url_for('api_keys'))

@app.route('/upload_corpus', methods=['POST'])
def upload_corpus():
    import zipfile
    file = request.files['corpus_file']
    if file:
        filename = file.filename
        filepath = os.path.join(CORPUS_DIR, filename)
        file.save(filepath)
        # If zip, extract to folder named after zip (without extension)
        if filename.lower().endswith('.zip'):
            folder_name = os.path.splitext(filename)[0]
            extract_path = os.path.join(CORPUS_DIR, folder_name)
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(filepath, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            os.remove(filepath)
            return jsonify({'status': 'success', 'folder': folder_name})
        return jsonify({'status': 'success', 'filename': filename})
    return jsonify({'status': 'error'})

@app.route('/process_corpus', methods=['POST'])
def process_corpus():
    provider = request.form.get('provider', 'ollama')
    model = request.form.get('model', 'llama2')
    corpus = request.form.get('corpus', CORPUS_DIR)
    llm = LLMProvider(provider, model, API_KEYS)
    processor = SimpleStoryProcessor(llm)
    results = process_entire_corpus(corpus, processor)
    viz_data = prepare_visualization_data(results)
    # Save with corpus/model in filename for switching
    result_name = f"{os.path.basename(corpus)}_{model}_visualization.json"
    json_file = export_for_html_visualization(viz_data, filename=result_name)
    return jsonify({'status': 'complete', 'json_file': str(json_file)})

# Streaming corpus processing endpoint
@app.route('/process_corpus_stream')
def process_corpus_stream():
    from flask import Response
    import json
    import time
    
    def generate():
        provider = request.args.get('provider', 'ollama')
        model = request.args.get('model', 'llama2')
        corpus = request.args.get('corpus', 'clean corpus no paratext')
        
        try:
            # Step 1: Scene Segmentation
            yield f"data: {json.dumps({'type': 'step_start', 'step': 1, 'message': 'Starting scene segmentation...'})}\n\n"
            
            corpus_path = os.path.join(CORPUS_DIR, corpus)
            if not os.path.exists(corpus_path):
                yield f"data: {json.dumps({'type': 'error', 'message': f'Corpus not found: {corpus}'})}\n\n"
                return
            
            # Simulate progress for scene segmentation
            for i in range(0, 101, 20):
                yield f"data: {json.dumps({'type': 'progress', 'step': 1, 'percentage': i, 'message': f'Processing scenes... {i}%'})}\n\n"
                time.sleep(0.5)
            
            yield f"data: {json.dumps({'type': 'step_complete', 'step': 1, 'message': 'Scene segmentation complete'})}\n\n"
            
            # Step 2: Goal & Conflict Analysis
            yield f"data: {json.dumps({'type': 'step_start', 'step': 2, 'message': 'Analyzing goals and conflicts...'})}\n\n"
            
            llm = LLMProvider(provider, model, API_KEYS if provider != 'ollama' else {})
            processor = SimpleStoryProcessor(llm)
            
            # This is where actual processing happens
            yield f"data: {json.dumps({'type': 'progress', 'step': 2, 'percentage': 10, 'message': 'Initializing LLM...'})}\n\n"
            
            results = process_entire_corpus(corpus_path, processor)
            
            yield f"data: {json.dumps({'type': 'progress', 'step': 2, 'percentage': 80, 'message': 'Analysis complete, processing results...'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'step': 2, 'percentage': 100, 'message': 'Goal and conflict analysis complete'})}\n\n"
            yield f"data: {json.dumps({'type': 'step_complete', 'step': 2, 'message': 'Analysis complete'})}\n\n"
            
            # Step 3: Visualization Preparation
            yield f"data: {json.dumps({'type': 'step_start', 'step': 3, 'message': 'Preparing visualization data...'})}\n\n"
            
            viz_data = prepare_visualization_data(results)
            yield f"data: {json.dumps({'type': 'progress', 'step': 3, 'percentage': 50, 'message': 'Generating visualization data...'})}\n\n"
            
            # Save with corpus/model in filename for switching
            result_name = f"{corpus.replace(' ', '_')}_{model}_visualization.json"
            json_file = export_for_html_visualization(viz_data, filename=result_name)
            
            yield f"data: {json.dumps({'type': 'progress', 'step': 3, 'percentage': 100, 'message': f'Saved to {result_name}'})}\n\n"
            yield f"data: {json.dumps({'type': 'step_complete', 'step': 3, 'message': 'Visualization data ready'})}\n\n"
            
            yield f"data: {json.dumps({'type': 'complete', 'message': 'All steps completed successfully', 'file': str(json_file)})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')


# List available corpus folders
@app.route('/list_corpora')
def list_corpora():
    return jsonify(get_corpus_folders())

# Serve visualization data for selected corpus
@app.route('/get_visualization_data')
def get_visualization_data():
    corpus = request.args.get('corpus')
    if not corpus:
        return jsonify({'error': 'No corpus specified'}), 400
    # Use path relative to corpus_uploads
    corpus_path = os.path.join(CORPUS_DIR, corpus)
    if not os.path.exists(corpus_path):
        return jsonify({'error': 'Corpus not found'}), 404
    # Process corpus and return visualization data
    provider = request.args.get('provider', 'ollama')
    model = request.args.get('model', 'llama2')
    llm = LLMProvider(provider, model, API_KEYS)
    processor = SimpleStoryProcessor(llm)
    results = process_entire_corpus(corpus_path, processor)
    viz_data = prepare_visualization_data(results)
    return jsonify(viz_data)

@app.route('/visualization')
def visualization():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True)

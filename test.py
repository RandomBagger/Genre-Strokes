from flask import Flask, request, redirect, url_for, render_template_string
import cloudinary
import cloudinary.uploader
import cloudinary.api
import os

# Load Cloudinary credentials from environment variables
cloudinary.config(
    cloud_name='dduqaae45',
    api_key='321868895363614',
    api_secret='G4PST28pDlgpcC9RDPYO2e8RFU8'
)

app = Flask(__name__)
# app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Limit upload size to 16 MB

@app.route('/')
def index():
    return redirect(url_for('upload_form'))

@app.route('/upload', methods=['POST'])
def upload():
    
    if 'files' not in request.files:
        return 'No file part', 400
    
    files = request.files.getlist('files')
    
    if not files:
        return 'No files selected', 400
    
    urls = []
    errors = []

    for file in files:
        if file.filename == '':
            errors.append('No selected file')
            continue
        
        if file:
            try:
                # Upload to Cloudinary
                response = cloudinary.uploader.upload(file)
                url = response['secure_url']
                urls.append(url)
            except Exception as e:
                errors.append(f'Error uploading file {file.filename}: {e}')

    # Construct the response
    response_html = '<h1>Files uploaded successfully!</h1>'
    
    if urls:
        response_html += '<ul>'
        for url in urls:
            response_html += f'<li><a href="{url}" target="_blank">View File</a></li>'
        response_html += '</ul>'
    
    if errors:
        response_html += '<h2>Errors:</h2><ul>'
        for error in errors:
            response_html += f'<li>{error}</li>'
        response_html += '</ul>'

    return render_template_string(response_html)

@app.route('/upload-form')
def upload_form():
    return '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Upload Media</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                h1 { color: #333; }
                form { max-width: 400px; margin: auto; }
                label, input, button { display: block; width: 100%; margin-bottom: 10px; }
                button { background-color: #007bff; color: white; border: none; padding: 10px; cursor: pointer; }
                button:hover { background-color: #0056b3; }
            </style>
        </head>
        <body>
            <h1>Upload Media to Cloudinary</h1>
            <form action="/upload" method="POST" enctype="multipart/form-data">
                <label for="files">Choose files:</label>
                <input type="file" id="files" name="files" accept="image/*,video/*" multiple required>
                <button type="submit">Upload</button>
            </form>
        </body>
        </html>
    '''

if __name__ == '__main__':
    app.run(debug=True)

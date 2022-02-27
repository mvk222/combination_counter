import os
import pandas as pd
from flask import Flask, send_file, flash, request, redirect, url_for, send_from_directory,render_template
from werkzeug.utils import secure_filename
from combination_counter.combination_counter import CombinationCounter
import shutil

UPLOAD_FOLDER = 'files_to_process'
ALLOWED_EXTENSIONS = {'xlsx'}

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 20 * 1000 * 1000

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if os.path.exists('files_to_process'):
            shutil.rmtree('files_to_process')
        os.makedirs('files_to_process')
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return redirect(url_for('load_and_process'))
    return render_template("upload.html")

@app.route('/load_and_process')
def load_and_process():
    for file in os.listdir("files_to_process"):
        if file.endswith(".xlsx"):
            df = pd.read_excel(f"files_to_process/{file}")
    counter = CombinationCounter()
    result = counter.count_combinations(df)
    result[result['count']>3].sort_values('count',ascending=False).reset_index(drop=True).to_csv(f"files_to_process/{file}.csv")
    return send_file(f"../files_to_process/{file}.csv", as_attachment=True)
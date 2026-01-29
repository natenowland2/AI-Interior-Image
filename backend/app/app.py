from flask import Flask, request, jsonify, send_file, current_app, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from openai import OpenAI
import json
from PIL import Image, ImageDraw
import io
import tempfile
import requests
from datetime import datetime
import sqlite3
from pathlib import Path
import re
import time
import uuid

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Ensure CORS is using the regex string for Vercel subdomains only
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Initialize OpenAI client
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not found in environment variables")

client = OpenAI(api_key=api_key)

# Create storage directory if it doesn't exist
STORAGE_DIR = Path(os.path.abspath(os.path.dirname(__file__))) / "stored_images"
STORAGE_DIR.mkdir(exist_ok=True)

print(f"Storage directory: {STORAGE_DIR}")

def get_absolute_url(filename):
    """Get absolute URL for a file"""
    return f"https://interior-image-generation.onrender.com/api/stored-image/{filename}"

# Database initialization
def init_db():
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS generated_images
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         original_path TEXT NOT NULL,
         generated_path TEXT NOT NULL,
         style TEXT NOT NULL,
         room_type TEXT NOT NULL,
         timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def save_image_from_url(url, filename):
    """Download and save image from URL"""
    response = requests.get(url)
    if response.status_code == 200:
        img_path = STORAGE_DIR / filename
        with open(img_path, 'wb') as f:
            f.write(response.content)
        return str(img_path)
    return None

def validate_stored_images():
    """Clean up database entries that don't have corresponding image files"""
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    
    # Get all entries
    c.execute('SELECT id, original_path, generated_path FROM generated_images')
    rows = c.fetchall()
    
    # Check each entry
    for row in rows:
        id, original_path, generated_path = row
        original_exists = (STORAGE_DIR / Path(original_path).name).exists()
        generated_exists = (STORAGE_DIR / Path(generated_path).name).exists()
        
        if not (original_exists and generated_exists):
            print(f"Removing invalid entry {id} due to missing files")
            c.execute('DELETE FROM generated_images WHERE id = ?', (id,))
    
    conn.commit()
    conn.close()

def store_generation_data(original_path, generated_path, style, room_type):
    """Store generation data in database"""
    # Verify both files exist before storing
    original_exists = (STORAGE_DIR / Path(original_path).name).exists()
    generated_exists = (STORAGE_DIR / Path(generated_path).name).exists()
    
    if not (original_exists and generated_exists):
        print("Warning: Not storing generation data because files don't exist")
        return False
        
    conn = sqlite3.connect('images.db')
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO generated_images
            (original_path, generated_path, style, room_type)
            VALUES (?, ?, ?, ?)
        ''', (original_path, generated_path, style, room_type))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error storing generation data: {str(e)}")
        return False
    finally:
        conn.close()

@app.route('/api/generations', methods=['GET'])
def get_generations():
    """Get all generated images history"""
    try:
        # First, clean up invalid entries
        validate_stored_images()
        
        conn = sqlite3.connect('images.db')
        c = conn.cursor()
        c.execute('''
            SELECT id, original_path, generated_path, style, room_type, timestamp
            FROM generated_images
            ORDER BY timestamp DESC
        ''')
        rows = c.fetchall()
        conn.close()

        generations = []
        for row in rows:
            original_filename = Path(row[1]).name
            generated_filename = Path(row[2]).name
            
            # Double check files exist before adding to response
            if (STORAGE_DIR / original_filename).exists() and (STORAGE_DIR / generated_filename).exists():
                generations.append({
                    'id': row[0],
                    'originalImage': get_absolute_url(original_filename),
                    'generatedImage': get_absolute_url(generated_filename),
                    'style': row[3],
                    'roomType': row[4],
                    'timestamp': row[5]
                })
        
        return jsonify(generations)
    except Exception as e:
        print(f"Error fetching generations: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/stored-image/<filename>')
def get_stored_image(filename):
    """Serve stored images"""
    try:
        response = send_file(
            STORAGE_DIR / filename,
            mimetype='image/jpeg'
        )
        # Add CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except FileNotFoundError as e:
        print(f"Image not found: {filename}")
        print(f"Storage directory contents: {list(STORAGE_DIR.glob('*'))}")
        return jsonify({'error': 'Image not found'}), 404
    except Exception as e:
        print(f"Error serving image: {str(e)}")
        return jsonify({'error': str(e)}), 500

def debug_image(stage, image):
    """Debug helper to print image information"""
    print(f"\n=== {stage} ===")
    print(f"Image mode: {image.mode}")
    print(f"Image size: {image.size}")
    print(f"Image format: {getattr(image, 'format', 'N/A')}")

def prepare_image_for_api(image_data, size=(1024, 1024)):
    """Prepare image for OpenAI API - must be square PNG."""
    try:
        # Open the image using PIL
        image = Image.open(io.BytesIO(image_data))
        debug_image("Original image", image)
        
        # Convert to RGBA
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
            debug_image("After RGBA conversion", image)
        
        # Calculate the target size while maintaining aspect ratio
        # We'll use the larger dimension to fill the square
        aspect = image.width / image.height
        if aspect > 1:
            # Wider than tall
            new_width = size[0]
            new_height = int(size[0] / aspect)
        else:
            # Taller than wide
            new_height = size[1]
            new_width = int(size[1] * aspect)
            
        # Resize the image
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        debug_image("After resize", image)
        
        # Create a square transparent background
        square = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Paste the resized image in the center
        paste_x = (size[0] - new_width) // 2
        paste_y = (size[1] - new_height) // 2
        square.paste(image, (paste_x, paste_y))
        debug_image("Final square image", square)
        
        # Save as PNG to bytes
        output = io.BytesIO()
        square.save(output, format='PNG')
        output.seek(0)
        
        # Print the first few bytes to verify PNG header
        print("First few bytes of PNG:", output.getvalue()[:8].hex())
        print(f"Total bytes in PNG: {len(output.getvalue())}")
        
        return output.getvalue()

    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise

def create_mask(size=(1024, 1024)):
    """Create a mask for the interior - must match image dimensions exactly."""
    try:
        # Create new image with transparent interior (area to edit)
        mask = Image.new('RGBA', size, (0, 0, 0, 0))
        
        # Calculate border width - about 5% of the image width
        border_width = size[0] // 20
        
        # Draw white borders (areas to preserve)
        draw = ImageDraw.Draw(mask)
        
        # Draw white frame
        draw.rectangle([0, 0, size[0], border_width], fill=(255, 255, 255, 255))  # Top
        draw.rectangle([0, size[1]-border_width, size[0], size[1]], fill=(255, 255, 255, 255))  # Bottom
        draw.rectangle([0, 0, border_width, size[1]], fill=(255, 255, 255, 255))  # Left
        draw.rectangle([size[0]-border_width, 0, size[0], size[1]], fill=(255, 255, 255, 255))  # Right
        
        # Save as PNG to bytes
        output = io.BytesIO()
        mask.save(output, format='PNG')
        output.seek(0)
        return output.getvalue()

    except Exception as e:
        print(f"Error creating mask: {str(e)}")
        raise

def get_style_prompt(style, room_type):
    """Generate a style-specific prompt for DALL-E."""
    # Strong base prompt for photorealism and preservation
    base_prompt = (
        "Ultra-realistic, photorealistic, high-resolution interior photograph. "
        "Maintain the original room structure: do not move, alter, or obscure the windows, doors, walls, ceiling, floor, or any architectural features. "
        "No text, people, or signage. ONLY add beautiful, magazine-quality furniture and decor. Use natural lighting, realistic shadows, and textures. Maintain the original perspective and brightness. "
    )

    # Room-specific centerpiece and furniture
    room_furniture = {
        "living room": "A modern, realistic sofa as the main centerpiece, with a designer coffee table, accent chairs, media console, plush area rug, throw pillows, modern wall art, side tables, a sculptural floor lamp, and other living room essentials.",
        "bedroom": "A realistic, luxurious bed as the main centerpiece, with premium bedding, modern nightstands, a sleek dresser, reading lamps, a soft area rug, elegant curtains, wall art, a cozy accent chair, a statement floor mirror, and other bedroom essentials.",
        "kitchen": "A realistic kitchen table and appliances as the main centerpiece, with designer chairs, modern bar stools, pendant lighting, a styled kitchen island, fruit bowl, premium small appliances, floating wall shelves, upscale kitchen textiles, and other kitchen essentials."
    }

    # Style-specific descriptions
    style_descriptions = {
        "modern minimalist": f"Arrange the furniture in a modern minimalist style: clean lines, neutral palette, uncluttered, open, airy, harmonious, and elegant.",
        "luxury classic": f"Arrange the furniture in a luxury classic style: rich materials, elegant details, sophisticated color palette, timeless and refined, with a sense of grandeur.",
        "scandinavian": f"Arrange the furniture in Scandinavian style: light woods, organic shapes, cozy textures, functional and inviting, with a bright and serene atmosphere.",
        "industrial": f"Arrange the furniture in industrial style: metal accents, raw materials, exposed elements, urban loft feel, and a bold, modern look.",
        "bohemian": f"Arrange the furniture in bohemian style: layered textiles, natural materials, eclectic mix, warm colors, and a relaxed, artistic vibe.",
        "contemporary": f"Arrange the furniture in contemporary style: current trends, comfortable pieces, balanced design, and a fresh, stylish ambiance."
    }

    furn = room_furniture.get(room_type, "appropriate furniture and decor")
    style_text = style_descriptions.get(style.lower(), "")
    full_prompt = base_prompt + furn + " " + style_text

    # Ensure prompt doesn't exceed 999 characters
    if len(full_prompt) > 999:
        full_prompt = full_prompt[:996] + "..."

    return full_prompt

@app.route('/api/generate-designs', methods=['POST'])
def generate_designs():
    temp_files = []  # Keep track of temporary files to clean up
    try:
        # Get style and image from request
        style = request.form.get('style', 'modern minimalist')
        room_type = request.form.get('roomType', 'living room')
        custom_prompt = request.form.get('customPrompt', '').strip()
        
        # Validate and normalize room type
        room_type_mapping = {
            'living': 'living room',
            'living room': 'living room',
            'bedroom': 'bedroom',
            'kitchen': 'kitchen'
        }
        room_type = room_type_mapping.get(room_type.lower(), 'living room')
        
        if 'image' not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        image_file = request.files['image']
        image_data = image_file.read()
        
        print("\n=== Starting design generation ===")
        print(f"Received style request: {style}")
        print(f"Received room type: {room_type}")
        print(f"Received image size: {len(image_data)} bytes")
        print(f"Original file content type: {image_file.content_type}")
        
        try:
            # Process image and create mask
            processed_image = prepare_image_for_api(image_data)
            mask_data = create_mask()
            
            # Save original image
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            original_filename = f"original_{timestamp}.jpg"
            original_path = STORAGE_DIR / original_filename
            
            # Save the original image
            with open(original_path, 'wb') as f:
                f.write(image_data)
            
            # Get detailed prompt for the style and room type
            base_prompt = get_style_prompt(style, room_type)
            
            # If custom prompt is provided, append it to the base prompt
            if custom_prompt:
                prompt = base_prompt + " " + custom_prompt
                # Ensure prompt doesn't exceed 999 characters
                if len(prompt) > 999:
                    prompt = prompt[:996] + "..."
            else:
                prompt = base_prompt
            
            print(f"\nUsing prompt: {prompt}")
            
            # Create temporary files for API request
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as image_temp, \
                 tempfile.NamedTemporaryFile(suffix='.png', delete=False) as mask_temp:
                
                # Write the processed images to temporary files
                image_temp.write(processed_image)
                mask_temp.write(mask_data)
                image_temp.flush()
                mask_temp.flush()
                
                # Store the file paths for cleanup
                temp_files.extend([image_temp.name, mask_temp.name])
            
            # Open files in a new context for the API request
            with open(temp_files[0], 'rb') as image_file, \
                 open(temp_files[1], 'rb') as mask_file:
                
                print("\n=== Making API Request ===")
                response = client.images.edit(
                    image=image_file,
                    mask=mask_file,
                    prompt=prompt,
                    n=1,
                    size="1024x1024",
                    model="dall-e-2"
                )
            
            print("\nSuccessfully received response from OpenAI")
            
            # Save generated image
            generated_filename = f"generated_{timestamp}.jpg"
            generated_path = save_image_from_url(response.data[0].url, generated_filename)
            
            if generated_path:
                # Store generation data in database
                if store_generation_data(
                    str(original_path),
                    generated_path,
                    style,
                    room_type
                ):
                    return jsonify({
                        "url": get_absolute_url(generated_filename),
                        "storedImage": get_absolute_url(generated_filename)
                    })
            
            return jsonify({"url": response.data[0].url})
            
        except Exception as api_error:
            error_message = str(api_error)
            print(f"\nFull API error: {error_message}")
            
            if "rate_limit" in error_message.lower():
                error_message = (
                    "Rate limit exceeded or insufficient credits. "
                    "Please check your OpenAI account billing status and try again later."
                )
            elif "invalid_api_key" in error_message.lower():
                error_message = "Invalid API key. Please check your OpenAI API key configuration."
            elif "invalid_request_error" in error_message.lower():
                error_message = "Invalid request. Please try again with different parameters."
            
            print(f"API Error: {error_message}")
            return jsonify({"error": f"API Error: {error_message}"}), 500
        
    except Exception as e:
        print(f"\n!!! Error occurred: {str(e)}")
        print(f"Error type: {type(e)}")
        return jsonify({"error": str(e)}), 500
        
    finally:
        # Clean up temporary files
        for temp_file in temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except Exception as e:
                print(f"Error cleaning up temporary file {temp_file}: {str(e)}")


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host='0.0.0.0', port=port) 
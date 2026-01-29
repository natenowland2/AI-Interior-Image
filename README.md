# DESIGNSPACE.AI - Interior Design Image Generator

![Demo UI](frontend/demo_ui.png)

An AI-powered interior design visualization tool that transforms empty or existing rooms into fully furnished spaces using OpenAI's DALL-E API. Upload a room photo and instantly generate photorealistic interior designs with customizable styles while preserving the room's architectural elements.

## 🎯 Overview

DESIGNSPACE.AI leverages advanced AI image editing capabilities to help users visualize interior design transformations. The application uses DALL-E 2's image editing API to add furniture and decor to room images while maintaining the original architectural structure, windows, doors, and lighting.

## ✨ Features

### Core Functionality

- **🎨 Multiple Design Styles**: Choose from 6 distinct interior design styles
  - Modern Minimalist
  - Luxury Classic
  - Scandinavian
  - Industrial
  - Bohemian
  - Contemporary

- **🏠 Room Type Support**: Optimized prompts for different room types
  - Living Room
  - Bedroom
  - Kitchen

- **🖼️ Image Upload & Preview**: 
  - Drag-and-drop or click to upload room images
  - Real-time image preview
  - Support for PNG, JPG, GIF up to 10MB

- **✏️ Custom Prompt Editor**: 
  - Add personalized transformation instructions
  - Combine with style and room type for unique designs
  - Examples: "add a fireplace", "use warm lighting", "include plants"

- **📚 Example Room Gallery**: 
  - Browse 8 pre-loaded example room images
  - Click to use examples directly for generation
  - Quick start without uploading your own image

- **💾 Generation History**: 
  - View all previous generations
  - Compare original and generated designs side-by-side
  - Track generation timestamps, styles, and room types

- **🔒 Architectural Preservation**: 
  - Maintains windows, doors, walls, ceiling, and floor
  - Preserves original lighting and perspective
  - Only adds furniture and decor, never removes structural elements

## 🏗️ Architecture

### System Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────┐
│   Frontend      │         │    Backend       │         │  OpenAI API  │
│   (Next.js)     │◄───────►│   (Flask)        │◄───────►│  (DALL-E 2) │
│                 │  HTTP   │                 │  REST   │              │
│  - React UI     │         │  - Image Proc   │         │  - Image Edit│
│  - State Mgmt    │         │  - Prompt Gen   │         │  - Generation│
│  - File Upload  │         │  - SQLite DB    │         │              │
└─────────────────┘         └──────────────────┘         └──────────────┘
```

### Frontend Architecture

**Technology Stack:**
- **Framework**: Next.js 15.3.1 with React 19
- **Styling**: Tailwind CSS 4
- **Language**: TypeScript
- **State Management**: React Hooks (useState, useEffect)

**Key Components:**
- `page.tsx`: Main application component with:
  - File upload handler
  - Image preview display
  - Custom prompt editor
  - Generation history modal
  - Example room gallery

**Layout Structure:**
- **Left Panel**: Main generation area with:
  - Generated image display
  - Loading progress indicator
  - Example room thumbnail gallery (3 columns)
- **Right Sidebar**: Controls panel with:
  - Room type selector
  - Design style selector
  - Image upload area
  - Custom prompt textarea
  - Generate button

### Backend Architecture

**Technology Stack:**
- **Framework**: Flask 2.0.1
- **Language**: Python 3
- **Database**: SQLite
- **Image Processing**: Pillow (PIL)
- **API Client**: OpenAI Python SDK

**Key Components:**

1. **Image Processing Pipeline**:
   - `prepare_image_for_api()`: Converts uploaded images to square PNG format (1024x1024) required by DALL-E
   - `create_mask()`: Generates border mask to preserve room structure
   - Maintains aspect ratio while centering image on transparent square

2. **Prompt Generation System**:
   - `get_style_prompt()`: Combines base prompt, room-specific furniture, and style descriptions
   - Custom prompt integration: Appends user-provided instructions
   - Character limit enforcement (999 chars for DALL-E 2)

3. **Data Persistence**:
   - SQLite database stores generation metadata
   - File system storage for original and generated images
   - Automatic cleanup of invalid database entries

4. **API Endpoints**:
   - `POST /api/generate-designs`: Main generation endpoint
   - `GET /api/generations`: Retrieve generation history
   - `GET /api/stored-image/<filename>`: Serve stored images

## 🔌 APIs Used

### OpenAI DALL-E 2 API

**Endpoint**: `client.images.edit()`

**Purpose**: Image editing and transformation

**Parameters**:
- `image`: Processed square PNG image (1024x1024)
- `mask`: Border mask to preserve room structure
- `prompt`: Combined style, room type, and custom instructions
- `n`: Number of images to generate (1)
- `size`: Image dimensions ("1024x1024")
- `model`: "dall-e-2"

**Response**: 
- URL to generated image
- Image downloaded and stored locally

**Rate Limits**: Subject to OpenAI API rate limits and billing

### Internal REST API

#### `POST /api/generate-designs`

**Request**:
- `image`: File (multipart/form-data)
- `style`: String (design style)
- `roomType`: String (room type)
- `customPrompt`: String (optional, custom instructions)

**Response**:
```json
{
  "url": "https://.../generated_image.jpg",
  "storedImage": "https://.../generated_image.jpg"
}
```

**Error Response**:
```json
{
  "error": "Error message"
}
```

#### `GET /api/generations`

**Response**:
```json
[
  {
    "id": 1,
    "originalImage": "https://.../original.jpg",
    "generatedImage": "https://.../generated.jpg",
    "style": "modern minimalist",
    "roomType": "living room",
    "timestamp": "2024-01-01 12:00:00"
  }
]
```

#### `GET /api/stored-image/<filename>`

**Response**: Image file (JPEG)

## 📝 Example Prompts

### Custom Prompt Examples

The custom prompt field allows you to add specific instructions that are appended to the base style prompt. Here are some effective examples:

**Furniture & Decor:**
- `"add a large sectional sofa in navy blue"`
- `"include a modern fireplace with a marble mantel"`
- `"add floor-to-ceiling bookshelves on one wall"`
- `"include a grand piano in the corner"`

**Lighting:**
- `"use warm, ambient lighting throughout"`
- `"add pendant lights above the dining area"`
- `"include floor lamps for cozy evening lighting"`
- `"use natural daylight from large windows"`

**Color & Atmosphere:**
- `"use a warm color palette with earth tones"`
- `"incorporate pops of emerald green and gold"`
- `"create a cozy, inviting atmosphere"`
- `"use cool tones with blue and gray accents"`

**Plants & Nature:**
- `"add large potted plants and greenery"`
- `"include a vertical garden wall"`
- `"add fresh flowers in vases throughout"`
- `"incorporate natural wood elements"`

**Textiles & Textures:**
- `"add plush area rugs and throw pillows"`
- `"include velvet and silk textures"`
- `"use layered textiles for depth"`
- `"add cozy blankets and cushions"`

**Special Features:**
- `"include a home office nook with a desk"`
- `"add a reading corner with an armchair"`
- `"create a bar area with wine storage"`
- `"include a breakfast nook by the window"`

### Combined Examples

**Modern Minimalist Living Room:**
- Base: Modern minimalist style with clean lines
- Custom: `"add a large sectional sofa, minimalist coffee table, and floor-to-ceiling plants"`

**Luxury Classic Bedroom:**
- Base: Luxury classic style with rich materials
- Custom: `"include a four-poster bed, velvet curtains, and a crystal chandelier"`

**Scandinavian Kitchen:**
- Base: Scandinavian style with light woods
- Custom: `"add open shelving, pendant lights, and fresh herbs on the counter"`

## 🚀 Setup & Installation

### Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/Interior-image-generation-main.git
cd Interior-image-generation-main
```

### Step 2: Backend Setup

1. Navigate to backend directory:
```bash
cd backend/app
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file:
```bash
echo "OPENAI_API_KEY=your_api_key_here" > .env
```

4. Start the Flask server:
```bash
python app.py
```

The backend will run on `http://localhost:5000` (or the port specified in your environment).

### Step 3: Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure API URL (optional):
Create `.env.local` file:
```
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

4. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

### Step 4: Access the Application

Open your browser and navigate to `http://localhost:3000`

## 📖 Usage Guide

### Basic Workflow

1. **Select Room Type**: Choose from Living Room, Bedroom, or Kitchen
2. **Choose Design Style**: Select one of the 6 available styles
3. **Upload Image**: 
   - Click the upload area or drag-and-drop an image
   - Or click an example room from the gallery below
4. **Add Custom Prompt** (Optional): Enter specific instructions for customization
5. **Generate**: Click "Generate Design" button
6. **View Result**: The generated design appears in the main display area
7. **View History**: Click "View History" to see all previous generations

### Tips for Best Results

- **Image Quality**: Use high-resolution images (at least 1024x1024 recommended)
- **Room Clarity**: Ensure the room is well-lit and clearly visible
- **Empty Rooms**: Works best with empty or minimally furnished rooms
- **Prompt Specificity**: Be specific in custom prompts for better results
- **Style Matching**: Choose a style that complements your room type

## 🛠️ Technology Stack

### Frontend
- **Next.js** 15.3.1 - React framework with server-side rendering
- **React** 19.0.0 - UI library
- **TypeScript** 5 - Type-safe JavaScript
- **Tailwind CSS** 4 - Utility-first CSS framework

### Backend
- **Flask** 2.0.1 - Python web framework
- **OpenAI** SDK 1.12.0+ - DALL-E API client
- **Pillow** - Image processing library
- **SQLite** - Lightweight database
- **Flask-CORS** - Cross-origin resource sharing

### Infrastructure
- **File Storage**: Local filesystem for image storage
- **Database**: SQLite for generation metadata
- **Image Format**: PNG for processing, JPEG for storage

## 📁 Project Structure

```
Interior-image-generation-main/
├── frontend/
│   ├── public/
│   │   └── rooms/          # Example room images
│   ├── src/
│   │   └── app/
│   │       ├── page.tsx    # Main application component
│   │       ├── layout.tsx  # Root layout
│   │       └── globals.css # Global styles
│   ├── demo_ui.png         # Demo screenshot
│   └── package.json
├── backend/
│   └── app/
│       ├── app.py          # Flask application
│       ├── requirements.txt # Python dependencies
│       ├── images.db       # SQLite database
│       └── stored_images/  # Generated images storage
└── README.md
```

## 🔧 Configuration

### Environment Variables

**Backend (.env)**:
```
OPENAI_API_KEY=your_openai_api_key_here
PORT=5000  # Optional, defaults to 5000
```

**Frontend (.env.local)**:
```
NEXT_PUBLIC_API_URL=http://localhost:5000/api
```

### Database

The SQLite database (`images.db`) is automatically created on first run. It stores:
- Generation ID
- Original image path
- Generated image path
- Style
- Room type
- Timestamp

## 🐛 Troubleshooting

### Common Issues

**Image not generating:**
- Check OpenAI API key is valid and has credits
- Verify image format is supported (PNG, JPG, GIF)
- Ensure image size is reasonable (< 10MB)

**CORS errors:**
- Verify backend CORS configuration allows your frontend origin
- Check API URL in frontend environment variables

**Database errors:**
- Delete `images.db` to reset the database
- Ensure write permissions in backend directory

**Image processing errors:**
- Verify Pillow is installed correctly
- Check image file is not corrupted

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🙏 Acknowledgments

- OpenAI for DALL-E 2 API
- Next.js and React communities
- Flask framework
- All contributors and users

---

**Built by Nate Nowland**

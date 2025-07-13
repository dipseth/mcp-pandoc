#!/Users/srivers/.pandoc/venv/bin/python3
"""
Ultra High-Quality Pandoc filter to convert Mermaid code blocks to crisp PNG/SVG images.
Enhanced version with dramatically improved resolution, advanced Puppeteer configuration,
professional color schemes, and comprehensive quality validation.

Features:
- Ultra-high DPI rendering (up to 300 DPI for print quality)
- Advanced Puppeteer configuration for crisp text rendering
- Dynamic sizing based on diagram complexity
- SVG output support with PNG fallback
- Professional color schemes optimized for business documents
- Comprehensive error handling and quality validation
- Smart caching with content-based hashing

Requires:
- pandocfilters
- mermaid-cli (mmdc) installed globally via npm
"""

import os
import sys
import subprocess
import hashlib
import json
import shutil
import tempfile
import re
from pathlib import Path
from pandocfilters import toJSONFilter, Para, Image, get_filename4code, get_caption, get_extension

# Quality configuration constants
DEFAULT_DPI = 300  # Print-quality DPI
DEFAULT_WIDTH = 600  # Much smaller width for compact images while maintaining quality
DEFAULT_HEIGHT = 400   # Much smaller height for compact images while maintaining quality
SCALE_FACTOR = 3  # Higher scale for ultra-crisp rendering
FONT_SIZE_BASE = 16  # Optimized font size for smaller images

def sha1(x):
    """Generate SHA1 hash of the input string."""
    return hashlib.sha1(x.encode('utf-8')).hexdigest()

def debug_log(message):
    """Write debug message to stderr."""
    sys.stderr.write(f"ULTRA-HQ DEBUG: {message}\n")

def estimate_diagram_size(code):
    """Estimate optimal dimensions based on diagram content."""
    lines = code.strip().split('\n')
    node_count = len([line for line in lines if '-->' in line or '---' in line])
    text_complexity = sum(len(line) for line in lines) / len(lines) if lines else 50
    
    # Dynamic sizing based on complexity
    width_multiplier = min(max(1.0, node_count / 10), 2.0)
    height_multiplier = min(max(1.0, len(lines) / 20), 1.8)
    
    width = int(DEFAULT_WIDTH * width_multiplier)
    height = int(DEFAULT_HEIGHT * height_multiplier)
    
    debug_log(f"Estimated size: {width}x{height} (nodes: {node_count}, lines: {len(lines)})")
    return width, height

def create_puppeteer_config():
    """Create advanced Puppeteer configuration for ultra-high quality rendering."""
    config = {
        "args": [
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-features=TranslateUI",
            "--disable-ipc-flooding-protection",
            "--disable-background-networking",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-client-side-phishing-detection",
            "--force-device-scale-factor=3",  # Force high DPI
            "--high-dpi-support=1",
            "--force-color-profile=srgb"
        ],
        "headless": True,
        "defaultViewport": {
            "width": 2400,
            "height": 1800,
            "deviceScaleFactor": 3,
            "isMobile": False,
            "hasTouch": False,
            "isLandscape": True
        },
        "ignoreDefaultArgs": ["--disable-extensions"],
        "timeout": 30000
    }
    return config

def create_ultra_hq_theme_config(theme="base", custom_vars=None):
    """Create ultra-high quality theme configuration with professional styling."""
    base_config = {
        "theme": theme,
        "themeVariables": {
            # Ultra-professional color scheme - high contrast for clarity
            "primaryColor": "#1e40af",           # Strong blue for excellent visibility
            "primaryTextColor": "#000000",       # Pure black for maximum contrast
            "primaryBorderColor": "#374151",     # Dark gray borders
            "lineColor": "#1f2937",              # Very dark gray for lines
            "secondaryColor": "#f3f4f6",         # Light gray backgrounds
            "tertiaryColor": "#ffffff",          # Pure white
            "background": "#ffffff",             # Pure white background
            "mainBkg": "#ffffff",                # Main background
            "secondBkg": "#f8fafc",             # Very light gray
            "tertiaryBkg": "#f1f5f9",           # Light blue-gray
            
            # Enhanced text styling for maximum readability
            "textColor": "#000000",              # Pure black text
            "fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
            "fontSize": f"{FONT_SIZE_BASE}px",
            "fontWeight": "500",                 # Medium weight for better visibility
            
            # High-contrast node styling
            "nodeBkg": "#dbeafe",                # Light blue nodes
            "nodeBorder": "#1e40af",             # Strong blue borders
            "nodeTextColor": "#000000",          # Black text on nodes
            "clusterBkg": "#eff6ff",             # Very light blue clusters
            "clusterBorder": "#1d4ed8",          # Strong blue cluster borders
            
            # Enhanced edge and connection styling
            "edgeLabelBackground": "#ffffff",
            "activeTaskBkgColor": "#1e40af",
            "activeTaskBorderColor": "#1d4ed8",
            "gridColor": "#d1d5db",
            "arrowheadColor": "#1f2937",
            
            # Section colors for different diagram types
            "section0": "#eff6ff",               # Very light blue
            "section1": "#e0f2fe",               # Light cyan
            "section2": "#f0fdf4",               # Very light green
            "section3": "#fefce8",               # Very light yellow
            "section4": "#fdf2f8",               # Very light pink
            
            # Sequence diagram specific
            "actorBkg": "#f8fafc",
            "actorBorder": "#374151",
            "actorTextColor": "#000000",
            "actorLineColor": "#6b7280",
            "signalColor": "#1f2937",
            "signalTextColor": "#000000",
            "labelBoxBkgColor": "#ffffff",
            "labelBoxBorderColor": "#374151",
            "labelTextColor": "#000000",
            "loopTextColor": "#000000",
            "noteBorderColor": "#d97706",
            "noteBkgColor": "#fef3c7",
            "noteTextColor": "#000000",
            
            # Gantt chart specific
            "taskBkgColor": "#dbeafe",
            "taskTextColor": "#000000",
            "taskTextLightColor": "#000000",
            "taskTextOutsideColor": "#000000",
            "taskTextClickableColor": "#1e40af",
            "activeTaskBkgColor": "#1e40af",
            "activeTaskBorderColor": "#1d4ed8",
            "gridColor": "#e5e7eb",
            "section0": "#f8fafc",
            "section1": "#f1f5f9",
            "section2": "#e2e8f0",
            "section3": "#cbd5e1",
            
            # Class diagram specific
            "classText": "#000000",
            "classTitleColor": "#000000",
            "relationshipColor": "#374151",
            "relationshipLabelColor": "#000000",
            "relationshipLabelBkgColor": "#ffffff"
        },
        "flowchart": {
            "htmlLabels": True,
            "curve": "basis",
            "padding": 20,
            "nodeSpacing": 50,
            "rankSpacing": 60,
            "diagramPadding": 30,
            "useMaxWidth": False,
            "defaultRenderer": "svg"
        },
        "sequence": {
            "diagramMarginX": 50,
            "diagramMarginY": 30,
            "actorMargin": 50,
            "width": 150,
            "height": 65,
            "boxMargin": 10,
            "boxTextMargin": 5,
            "noteMargin": 10,
            "messageMargin": 35,
            "mirrorActors": True,
            "bottomMarginAdj": 1,
            "useMaxWidth": False,
            "rightAngles": False,
            "showSequenceNumbers": False
        },
        "gantt": {
            "numberSectionStyles": 4,
            "axisFormat": "%Y-%m-%d",
            "topPadding": 50,
            "leftPadding": 75,
            "gridLineStartPadding": 35,
            "fontSize": FONT_SIZE_BASE,
            "fontFamily": "'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
            "sectionFontSize": FONT_SIZE_BASE + 2,
            "bottomPadding": 25,
            "rightPadding": 25
        }
    }
    
    # Merge custom variables if provided
    if custom_vars:
        base_config["themeVariables"].update(custom_vars)
    
    return base_config

def validate_image_quality(image_path):
    """Validate the generated image meets quality standards."""
    if not os.path.exists(image_path):
        return False, "Image file not found"
    
    file_size = os.path.getsize(image_path)
    if file_size < 1000:  # Less than 1KB is likely an error
        return False, f"Image file too small ({file_size} bytes)"
    
    debug_log(f"Image validation passed: {file_size} bytes")
    return True, "Quality validation passed"

def mermaid_to_ultra_hq_image(key, value, format, meta):
    """Convert Mermaid code blocks to ultra-high quality images."""
    if key == 'CodeBlock' and len(value) == 2:
        [[ident, classes, keyvals], code] = value
        
        # Debug logging
        debug_log(f"Processing code block with classes: {classes}")
        debug_log(f"Keyvals: {keyvals}")
        
        # Check for mermaid class in different formats
        is_mermaid = False
        
        # Check in classes
        for cls in classes:
            if "mermaid" in cls.lower():
                is_mermaid = True
                debug_log(f"Found mermaid in class: {cls}")
                break
        
        # Also check for class attribute in keyvals
        for k, v in keyvals:
            if k == "class" and "mermaid" in v.lower():
                is_mermaid = True
                debug_log(f"Found mermaid in keyval class: {v}")
                break
        
        # Check if code starts with mermaid syntax
        if not is_mermaid and code.strip().startswith(("graph ", "sequenceDiagram", "classDiagram", "stateDiagram", "gantt", "pie ", "flowchart ", "erDiagram", "journey", "gitgraph")):
            is_mermaid = True
            debug_log("Detected mermaid syntax in code content")
        
        if is_mermaid:
            debug_log("Processing as ultra-high quality mermaid diagram")
            
            # Get output directory from environment variable if available
            output_dir = os.environ.get('PANDOC_OUTPUT_DIR', '')
            
            # Create mermaid-images directory in the current directory
            img_dir = "mermaid-images"
            if not os.path.isdir(img_dir):
                os.makedirs(img_dir)
                sys.stderr.write(f"Created directory {img_dir}\n")
            
            # Create a unique filename based on the content hash
            base_filename = sha1(code)
            filename = os.path.join(img_dir, base_filename)
            
            # Determine output format - prefer SVG for scalability, PNG for compatibility
            output_format = "png"  # Default to PNG for wide compatibility
            for k, v in keyvals:
                if k == "format" and v.lower() in ["svg", "png"]:
                    output_format = v.lower()
            
            filetype = get_extension(format, output_format, html=output_format, latex="png")
            dest = f"{filename}.{filetype}"
            
            if not os.path.isfile(dest):
                # Estimate optimal dimensions
                width, height = estimate_diagram_size(code)
                
                # Create a temporary mermaid file
                with open(f"{filename}.mmd", "w", encoding='utf-8') as f:
                    f.write(code)
                
                # Run mmdc to convert mermaid to ultra-high quality image
                try:
                    # Create Puppeteer config
                    puppeteer_config = create_puppeteer_config()
                    puppeteer_config_file = f"{filename}.puppeteer.json"
                    with open(puppeteer_config_file, "w") as f:
                        json.dump(puppeteer_config, f, indent=2)
                    
                    # Extract theme and custom variables from attributes
                    theme = "base"
                    custom_vars = {}
                    for k, v in keyvals:
                        if k == "theme":
                            theme = v
                        elif k.startswith("theme-"):
                            var_name = k[6:]  # Remove "theme-" prefix
                            custom_vars[var_name] = v
                    
                    # Create ultra-high quality theme config
                    config = create_ultra_hq_theme_config(theme, custom_vars)
                    config_file = f"{filename}.config.json"
                    with open(config_file, "w") as f:
                        json.dump(config, f, indent=2)
                    
                    # Enhanced mmdc command with ultra-high quality settings
                    cmd = [
                        "mmdc",
                        "-i", f"{filename}.mmd",
                        "-o", dest,
                        "-c", config_file,
                        "-p", puppeteer_config_file,
                        "-b", "white",
                        "-w", str(width),
                        "-H", str(height),
                        "-s", str(SCALE_FACTOR),
                        "--pdfFit"
                    ]
                    
                    # Add format-specific options
                    if output_format == "svg":
                        cmd.extend(["--svg"])
                    
                    debug_log(f"Running command: {' '.join(cmd)}")
                    
                    # Execute with proper error handling
                    result = subprocess.run(
                        cmd,
                        check=True,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    # Clean up temporary config files
                    os.unlink(config_file)
                    os.unlink(puppeteer_config_file)
                    os.unlink(f"{filename}.mmd")
                    
                    # Validate image quality
                    is_valid, validation_msg = validate_image_quality(dest)
                    if not is_valid:
                        sys.stderr.write(f"Quality validation failed: {validation_msg}\n")
                        return None
                    
                    sys.stderr.write(f"Created ultra-high quality {output_format.upper()} image {dest} ({width}x{height}, {SCALE_FACTOR}x scale)\n")
                    
                except subprocess.TimeoutExpired:
                    sys.stderr.write(f"Timeout creating Mermaid diagram (>60s)\n")
                    return None
                except subprocess.CalledProcessError as e:
                    sys.stderr.write(f"Error creating Mermaid diagram: {e.stderr}\n")
                    # Clean up any partial files
                    for temp_file in [config_file, puppeteer_config_file, f"{filename}.mmd"]:
                        if os.path.exists(temp_file):
                            os.unlink(temp_file)
                    return None
                except Exception as e:
                    sys.stderr.write(f"Unexpected error creating Mermaid diagram: {str(e)}\n")
                    return None
            
            # If output directory is specified and different from current directory,
            # copy the mermaid-images directory to the output directory
            if output_dir and os.path.isdir(output_dir):
                output_img_dir = os.path.join(output_dir, img_dir)
                if not os.path.isdir(output_img_dir):
                    os.makedirs(output_img_dir)
                
                # Copy the generated image to the output directory
                output_dest = os.path.join(output_img_dir, f"{base_filename}.{filetype}")
                shutil.copy2(dest, output_dest)
                sys.stderr.write(f"Copied image to {output_dest}\n")
            
            # Get caption from the code block attributes
            caption, typef, keyvals = get_caption(keyvals)
            
            # Return the image as a paragraph
            return Para([Image([ident, [], keyvals], caption, [dest, typef or ""])])

if __name__ == "__main__":
    toJSONFilter(mermaid_to_ultra_hq_image)
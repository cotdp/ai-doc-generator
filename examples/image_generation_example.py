#!/usr/bin/env python
"""
Example script demonstrating how to use the ImageGenerationAgent.
"""

import os
import sys
import asyncio
import argparse
from dotenv import load_dotenv

# Add the parent directory to the path so we can import from src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.image_generation_agent import ImageGenerationAgent

# Load environment variables from .env.local or .env
load_dotenv(".env.local")
if not os.getenv("OPENAI_API_KEY"):
    load_dotenv(".env")

async def generate_single_image(description, caption, size, quality, style):
    """Generate a single image using the ImageGenerationAgent."""
    print(f"Generating image: {caption}")
    print(f"Description: {description}")
    print(f"Settings: size={size}, quality={quality}, style={style}")
    
    agent = ImageGenerationAgent()
    task = {
        "description": description,
        "caption": caption,
        "size": size,
        "quality": quality,
        "style": style
    }
    
    result = await agent.execute(task)
    
    if result["success"]:
        print(f"Image generated successfully: {result['image_path']}")
        return result["image_path"]
    else:
        print(f"Image generation failed: {result.get('error', 'Unknown error')}")
        return None

async def generate_batch_images(descriptions, size, quality, style):
    """Generate multiple images in batch using the ImageGenerationAgent."""
    print(f"Generating {len(descriptions)} images in batch")
    print(f"Settings: size={size}, quality={quality}, style={style}")
    
    agent = ImageGenerationAgent()
    task = {
        "batch": True,
        "descriptions": descriptions,
        "size": size,
        "quality": quality,
        "style": style
    }
    
    result = await agent.execute(task)
    
    if result["success"]:
        print(f"Batch generation completed:")
        print(f"  - Total: {result['total']}")
        print(f"  - Successful: {result['successful']}")
        print(f"  - Failed: {result['failed']}")
        
        for path in result["image_paths"]:
            print(f"  - {path}")
            
        return result["image_paths"]
    else:
        print("Batch generation failed completely")
        return []

async def main():
    """Main function to run examples."""
    parser = argparse.ArgumentParser(description="Image Generation Agent Example")
    parser.add_argument("--batch", action="store_true", help="Run batch generation example")
    parser.add_argument("--size", default="1024x1024", help="Image size (e.g., 1024x1024, 1792x1024)")
    parser.add_argument("--quality", default="standard", choices=["standard", "hd"], help="Image quality")
    parser.add_argument("--style", default="abstract", 
                        choices=["abstract", "realistic", "diagram", "infographic", "artistic"], 
                        help="Image style")
    args = parser.parse_args()
    
    if args.batch:
        # Example of batch generation
        descriptions = [
            ("A flowchart showing the process of AI-assisted document creation, with clear steps from planning to final output", 
             "AI Document Creation Process"),
             
            ("A diagram illustrating the components of a modern AI system, including data inputs, processing layers, and outputs", 
             "AI System Architecture"),
             
            ("An infographic showing the benefits of AI document generation for businesses, with statistics and key points", 
             "AI Document Generation Benefits")
        ]
        
        await generate_batch_images(descriptions, args.size, args.quality, args.style)
    else:
        # Example of single image generation
        description = "A visualization of artificial intelligence creating documentation, shown as a futuristic process with flowing data and document outputs"
        caption = "AI Documentation Generation"
        
        await generate_single_image(description, caption, args.size, args.quality, args.style)

if __name__ == "__main__":
    asyncio.run(main()) 
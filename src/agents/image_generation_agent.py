import asyncio
import os
from typing import Any, Dict, List, Optional, Tuple

import aiohttp
from openai import OpenAI
from slugify import slugify

from .base_agent import BaseAgent


class ImageGenerationAgent(BaseAgent):
    """Agent responsible for generating images using AI."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
        image_model: str = "dall-e-3",
    ):
        """Initialize the image generation agent.

        Args:
            model (str): The text model to use for the agent
            temperature (float): The temperature for model responses
            image_model (str): The image generation model to use
        """
        super().__init__(model, temperature)
        self.image_model = image_model
        self.output_dir = os.getenv("IMAGE_OUTPUT_DIR", "output/images")

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        # Get API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")

    async def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the image generation task.

        Args:
            task (Dict[str, Any]): The task parameters, which should include:
                - description (str): Description of the image to generate
                - caption (str, optional): Caption for the image
                - size (str, optional): Size of the image, default is "1792x1024"
                - quality (str, optional): Quality of the image, default is "standard"
                - style (str, optional): Style of the image, default is "abstract"
                - batch (bool, optional): Whether to generate images in batch
                - descriptions (List[Tuple[str, str]], optional): List of (description, caption) pairs for batch generation

        Returns:
            Dict[str, Any]: The task results, which include:
                - success (bool): Whether the generation was successful
                - image_path (str, optional): Path to the generated image
                - image_paths (List[str], optional): Paths to the generated images for batch generation
                - error (str, optional): Error message if generation failed
        """
        self.logger.info("Starting image generation task")

        # Check for batch generation
        if task.get("batch", False) and "descriptions" in task:
            self.logger.info(
                f"Batch image generation requested for {len(task['descriptions'])} images"
            )
            return await self._batch_generate_images(
                task["descriptions"],
                task.get("size", "1792x1024"),
                task.get("quality", "standard"),
                task.get("style", "abstract"),
            )

        # Single image generation
        description = task.get("description")
        if not description:
            return {"success": False, "error": "No description provided"}

        caption = task.get("caption", "Generated Image")
        size = task.get("size", "1792x1024")
        quality = task.get("quality", "standard")
        style = task.get("style", "abstract")

        image_path = await self.generate_image(
            description, caption, size, quality, style
        )

        if image_path:
            return {"success": True, "image_path": image_path}
        else:
            return {"success": False, "error": "Failed to generate image"}

    async def generate_image(
        self,
        description: str,
        caption: str,
        size: str = "1792x1024",
        quality: str = "standard",
        style: str = "abstract",
    ) -> Optional[str]:
        """Generate and save an image based on the description.

        Args:
            description (str): The description of the image to generate
            caption (str): Caption for the image (used for filename)
            size (str): Size of the image (e.g., "1024x1024", "1792x1024", "1024x1792")
            quality (str): Quality of the image ("standard" or "hd")
            style (str): Style preference for the image ("abstract", "realistic", "diagram", etc.)

        Returns:
            Optional[str]: Path to the saved image, or None if generation failed
        """
        # Input validation
        if not description or len(description) < 10:
            self.logger.error("Image description is too short or empty")
            return None

        self.logger.debug(f"Generating image for caption: {caption}")
        self.logger.debug(f"Using description: {description}")

        try:
            # Configure OpenAI client
            client = OpenAI(api_key=self.api_key)

            # Construct prompt based on style
            prompt = self._construct_prompt(description, style)

            # Generate image
            self.logger.debug(f"Calling {self.image_model} API to generate image")
            response = client.images.generate(
                model=self.image_model, prompt=prompt, n=1, size=size, quality=quality
            )

            if not response.data:
                self.logger.error("No image data received from API")
                return None

            image_url = response.data[0].url
            self.logger.debug(f"Image generated successfully, URL: {image_url}")

            # Download and save image
            filename = f"{slugify(caption)}.png"
            path = os.path.join(self.output_dir, filename)

            self.logger.debug(f"Downloading image to: {path}")
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    if resp.status != 200:
                        self.logger.error(
                            f"Failed to download image: HTTP {resp.status}"
                        )
                        return None

                    with open(path, "wb") as f:
                        f.write(await resp.read())

            self.logger.debug("Image saved successfully")
            return path

        except Exception as e:
            self.logger.error(f"Error generating/saving image: {str(e)}")
            return None

    async def _batch_generate_images(
        self,
        descriptions: List[Tuple[str, str]],
        size: str = "1792x1024",
        quality: str = "standard",
        style: str = "abstract",
    ) -> Dict[str, Any]:
        """Generate multiple images concurrently.

        Args:
            descriptions (List[Tuple[str, str]]): List of (description, caption) pairs
            size (str): Size of the images
            quality (str): Quality of the images
            style (str): Style preference for the images

        Returns:
            Dict[str, Any]: Results of the batch generation
        """
        self.logger.info(f"Generating {len(descriptions)} images in batch")

        # Create tasks for each image
        tasks = [
            self.generate_image(desc, caption, size, quality, style)
            for desc, caption in descriptions
        ]

        # Run tasks concurrently
        results = await asyncio.gather(*tasks)

        # Filter out failed generations
        successful_paths = [path for path in results if path is not None]
        failed_count = len(descriptions) - len(successful_paths)

        self.logger.info(
            f"Batch generation completed: {len(successful_paths)} successful, {failed_count} failed"
        )

        return {
            "success": len(successful_paths) > 0,
            "image_paths": successful_paths,
            "total": len(descriptions),
            "successful": len(successful_paths),
            "failed": failed_count,
        }

    def _construct_prompt(self, description: str, style: str) -> str:
        """Construct a prompt for image generation based on the style.

        Args:
            description (str): The base description
            style (str): The style preference

        Returns:
            str: The constructed prompt
        """
        base_prompt = f"{description}"

        style_modifiers = {
            "abstract": "Create an abstract, conceptual visualization. Make it visually striking with modern design elements. The image should be artistic and symbolic, avoiding any explicit text or labels. Use visual metaphors and creative symbolism to convey the concept.",
            "realistic": "Create a photorealistic visualization with high detail and natural lighting. The image should appear lifelike and convincing, as if captured by a professional photographer.",
            "diagram": "Create a clear, professional diagram with clean lines and distinct elements. Use a simple color scheme with good contrast to ensure readability. The diagram should effectively communicate the structural or process relationships.",
            "infographic": "Create a modern infographic style visualization with a clean layout. Use a consistent color scheme, simple icons, and minimal design elements to communicate information clearly and effectively.",
            "artistic": "Create an artistic interpretation with creative use of color, composition, and style. The image should be visually appealing and evocative, with an emphasis on aesthetic quality.",
        }

        # Get style modifier or use abstract as default
        modifier = style_modifiers.get(style.lower(), style_modifiers["abstract"])

        return f"{base_prompt}. {modifier}"

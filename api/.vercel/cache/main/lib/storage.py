"""Vercel Blob storage utility for file uploads."""

from vercel_blob import put, del_
from io import BytesIO
from PIL import Image
import uuid
from config import settings


class StorageService:
    """Service for managing Vercel Blob storage."""

    async def upload_image(
        self,
        file_data: bytes,
        filename: str,
        user_id: str,
        content_type: str = "image/png"
    ) -> dict:
        """
        Upload image to Vercel Blob storage.

        Args:
            file_data: Raw image bytes
            filename: Original filename
            user_id: User ID for organization
            content_type: MIME type

        Returns:
            Dict with url, thumbnail_url, width, height, file_size
        """
        # Validate image and get dimensions
        image = Image.open(BytesIO(file_data))
        width, height = image.size
        file_size = len(file_data)

        # Generate unique filename
        ext = filename.split(".")[-1].lower()
        unique_filename = f"{user_id}/{uuid.uuid4()}.{ext}"

        # Upload original
        blob = await put(unique_filename, file_data, {
            "content_type": content_type,
            "access": "public"
        })

        # Generate thumbnail (max 300px width)
        thumbnail_data = self._generate_thumbnail(image)
        thumb_filename = f"{user_id}/thumb_{uuid.uuid4()}.{ext}"
        thumb_blob = await put(thumb_filename, thumbnail_data, {
            "content_type": content_type,
            "access": "public"
        })

        return {
            "url": blob.url,
            "thumbnail_url": thumb_blob.url,
            "width": width,
            "height": height,
            "file_size": file_size
        }

    def _generate_thumbnail(self, image: Image, max_size: int = 300) -> bytes:
        """Generate thumbnail from image."""
        img_copy = image.copy()

        # Calculate new dimensions maintaining aspect ratio
        if img_copy.width > img_copy.height:
            new_width = max_size
            new_height = int(max_size * img_copy.height / img_copy.width)
        else:
            new_height = max_size
            new_width = int(max_size * img_copy.width / img_copy.height)

        img_copy.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = BytesIO()
        img_copy.save(output, format="PNG", optimize=True)
        return output.getvalue()

    async def delete_file(self, url: str):
        """Delete file from Vercel Blob storage."""
        try:
            await del_(url)
        except Exception as e:
            print(f"Failed to delete file: {e}")


# Singleton instance
storage_service = StorageService()

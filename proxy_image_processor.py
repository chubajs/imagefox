#!/usr/bin/env python3
"""
Enhanced image processor with DataImpulse proxy support for ImageFox.
Handles image downloads through rotating proxies to avoid rate limiting and blocks.
"""

import asyncio
import logging
import hashlib
import tempfile
import random
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

import aiohttp
import aiofiles
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from proxy_config import DataImpulseConfig

logger = logging.getLogger(__name__)


@dataclass
class ProxyDownloadResult:
    """Result of a proxy download attempt."""
    url: str
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    download_time: Optional[float] = None
    proxy_used: Optional[str] = None
    error: Optional[str] = None
    retry_count: int = 0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ProxyImageProcessor:
    """
    Enhanced image processor with proxy rotation support.
    Uses DataImpulse proxies to download images reliably.
    """
    
    def __init__(
        self,
        proxy_config: Optional[DataImpulseConfig] = None,
        temp_dir: Optional[str] = None,
        max_file_size: int = 50 * 1024 * 1024,  # 50MB
        min_dimensions: Tuple[int, int] = (100, 100),
        max_dimensions: Tuple[int, int] = (10000, 10000),
        supported_formats: Optional[List[str]] = None,
        concurrent_downloads: int = 5,
        use_proxy: bool = True,
        proxy_countries: Optional[List[str]] = None
    ):
        self.proxy_config = proxy_config or DataImpulseConfig()
        self.temp_dir = Path(temp_dir or tempfile.gettempdir()) / "imagefox_proxy"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_file_size = max_file_size
        self.min_dimensions = min_dimensions
        self.max_dimensions = max_dimensions
        self.supported_formats = supported_formats or ['JPEG', 'PNG', 'WEBP', 'GIF']
        self.concurrent_downloads = concurrent_downloads
        self.use_proxy = use_proxy
        self.proxy_countries = proxy_countries or ['us', 'uk', 'de', None]  # None = random country
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.download_stats = {
            'total_attempts': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'proxy_failures': 0,
            'total_bytes': 0,
            'total_time': 0.0
        }
        
        logger.info(f"ProxyImageProcessor initialized with proxy: {use_proxy}")
    
    async def __aenter__(self):
        """Enter async context."""
        connector = aiohttp.TCPConnector(limit=self.concurrent_downloads, force_close=True)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        
        # Test proxy connectivity
        if self.use_proxy:
            await self._test_proxy_connection()
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context."""
        if self.session:
            await self.session.close()
        
        # Log statistics
        logger.info(f"Download statistics: {self.download_stats}")
    
    async def _test_proxy_connection(self) -> bool:
        """Test proxy connection with IP check."""
        try:
            proxy_url = self.proxy_config.get_rotating_http_url()
            
            async with self.session.get(
                "https://api.ipify.org/",
                proxy=proxy_url
            ) as response:
                if response.status == 200:
                    ip = await response.text()
                    logger.info(f"Proxy test successful, external IP: {ip.strip()}")
                    return True
        except Exception as e:
            logger.warning(f"Proxy test failed: {e}")
            
        return False
    
    def _get_random_proxy(self) -> str:
        """Get a random proxy configuration."""
        country = random.choice(self.proxy_countries)
        return self.proxy_config.get_rotating_http_url(country)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def _download_with_proxy(self, url: str, session_id: Optional[int] = None) -> ProxyDownloadResult:
        """
        Download image using proxy with retry logic.
        
        Args:
            url: Image URL to download
            session_id: Optional session ID for sticky proxy
            
        Returns:
            ProxyDownloadResult with download details
        """
        start_time = datetime.now()
        proxy_url = None
        
        try:
            # Choose proxy strategy
            if session_id is not None:
                # Use sticky session for related downloads
                proxy_url = self.proxy_config.get_sticky_http_url(session_id=session_id)
            else:
                # Use rotating proxy with random country
                proxy_url = self._get_random_proxy()
            
            # Prepare request kwargs
            kwargs = {}
            if self.use_proxy:
                kwargs['proxy'] = proxy_url
            
            # Download image
            async with self.session.get(url, **kwargs) as response:
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '')
                if not content_type.startswith('image/'):
                    raise ValueError(f"Invalid content type: {content_type}")
                
                # Check file size
                content_length = response.headers.get('content-length')
                if content_length and int(content_length) > self.max_file_size:
                    raise ValueError(f"File too large: {content_length} bytes")
                
                # Download to temp file
                content = await response.read()
                
                # Generate unique filename
                file_hash = hashlib.md5(content).hexdigest()
                extension = self._get_extension_from_url(url) or '.jpg'
                file_path = self.temp_dir / f"{file_hash}{extension}"
                
                # Save file
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(content)
                
                download_time = (datetime.now() - start_time).total_seconds()
                
                # Update statistics
                self.download_stats['successful_downloads'] += 1
                self.download_stats['total_bytes'] += len(content)
                self.download_stats['total_time'] += download_time
                
                return ProxyDownloadResult(
                    url=url,
                    success=True,
                    file_path=str(file_path),
                    file_size=len(content),
                    download_time=download_time,
                    proxy_used=proxy_url if self.use_proxy else "direct"
                )
                
        except Exception as e:
            self.download_stats['failed_downloads'] += 1
            if proxy_url:
                self.download_stats['proxy_failures'] += 1
            
            logger.error(f"Download failed for {url}: {e}")
            
            return ProxyDownloadResult(
                url=url,
                success=False,
                error=str(e),
                proxy_used=proxy_url if self.use_proxy else "direct"
            )
        
        finally:
            self.download_stats['total_attempts'] += 1
    
    async def download_images(
        self,
        urls: List[str],
        session_id: Optional[int] = None
    ) -> List[ProxyDownloadResult]:
        """
        Download multiple images concurrently.
        
        Args:
            urls: List of image URLs
            session_id: Optional session ID for sticky proxy
            
        Returns:
            List of download results
        """
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        # Create download tasks
        tasks = []
        for url in urls:
            task = self._download_with_proxy(url, session_id)
            tasks.append(task)
        
        # Execute concurrently with semaphore
        semaphore = asyncio.Semaphore(self.concurrent_downloads)
        
        async def download_with_limit(task):
            async with semaphore:
                return await task
        
        results = await asyncio.gather(
            *[download_with_limit(task) for task in tasks],
            return_exceptions=True
        )
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(ProxyDownloadResult(
                    url=urls[i],
                    success=False,
                    error=str(result)
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def validate_image(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate downloaded image.
        
        Args:
            file_path: Path to image file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Open and validate image
            with Image.open(file_path) as img:
                # Check format
                if img.format not in self.supported_formats:
                    return False, f"Unsupported format: {img.format}"
                
                # Check dimensions
                width, height = img.size
                min_w, min_h = self.min_dimensions
                max_w, max_h = self.max_dimensions
                
                if width < min_w or height < min_h:
                    return False, f"Image too small: {width}x{height}"
                
                if width > max_w or height > max_h:
                    return False, f"Image too large: {width}x{height}"
                
                return True, None
                
        except Exception as e:
            return False, f"Image validation failed: {e}"
    
    async def process_and_download(
        self,
        urls: List[str],
        validate: bool = True
    ) -> List[ProxyDownloadResult]:
        """
        Download and validate images.
        
        Args:
            urls: List of image URLs
            validate: Whether to validate downloaded images
            
        Returns:
            List of download results with validation
        """
        # Download images
        results = await self.download_images(urls)
        
        # Validate if requested
        if validate:
            for result in results:
                if result.success and result.file_path:
                    is_valid, error = await self.validate_image(result.file_path)
                    if not is_valid:
                        result.success = False
                        result.error = error
                        # Remove invalid file
                        try:
                            Path(result.file_path).unlink()
                        except:
                            pass
        
        return results
    
    def _get_extension_from_url(self, url: str) -> Optional[str]:
        """Extract file extension from URL."""
        try:
            path = url.split('?')[0].split('#')[0]
            if '.' in path:
                ext = '.' + path.split('.')[-1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                    return ext
        except:
            pass
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get download statistics."""
        stats = self.download_stats.copy()
        
        # Calculate additional metrics
        if stats['successful_downloads'] > 0:
            stats['avg_download_time'] = stats['total_time'] / stats['successful_downloads']
            stats['avg_file_size'] = stats['total_bytes'] / stats['successful_downloads']
        
        if stats['total_attempts'] > 0:
            stats['success_rate'] = stats['successful_downloads'] / stats['total_attempts']
            
        return stats
    
    async def cleanup(self):
        """Clean up temporary files."""
        try:
            for file_path in self.temp_dir.glob("*"):
                file_path.unlink()
            logger.info(f"Cleaned up temporary files in {self.temp_dir}")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


async def test_proxy_downloader():
    """Test the proxy image downloader."""
    # Test URLs (using public sample images)
    test_urls = [
        "https://picsum.photos/800/600",
        "https://via.placeholder.com/600x400",
        "https://dummyimage.com/1024x768/000/fff"
    ]
    
    async with ProxyImageProcessor(use_proxy=True) as processor:
        print("Testing proxy image downloads...")
        
        results = await processor.process_and_download(test_urls, validate=True)
        
        for result in results:
            if result.success:
                print(f"✓ Downloaded: {result.url}")
                print(f"  File: {result.file_path}")
                print(f"  Size: {result.file_size:,} bytes")
                print(f"  Time: {result.download_time:.2f}s")
                print(f"  Proxy: {result.proxy_used}")
            else:
                print(f"✗ Failed: {result.url}")
                print(f"  Error: {result.error}")
        
        print("\nStatistics:")
        stats = processor.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        await processor.cleanup()


if __name__ == "__main__":
    asyncio.run(test_proxy_downloader())
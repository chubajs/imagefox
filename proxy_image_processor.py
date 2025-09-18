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
import time
from urllib.parse import urlparse

import aiohttp
import aiofiles
from PIL import Image
from tenacity import retry, stop_after_attempt, wait_exponential

from proxy_config import DataImpulseConfig

logger = logging.getLogger(__name__)


class BrowserHeaders:
    """Generate realistic browser headers for web scraping obfuscation."""
    
    USER_AGENTS = [
        # Chrome on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        
        # Chrome on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
        
        # Firefox on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        
        # Safari on macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        
        # Edge on Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    @classmethod
    def get_random_headers(cls, url: str) -> Dict[str, str]:
        """Generate random realistic browser headers."""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        headers = {
            "User-Agent": random.choice(cls.USER_AGENTS),
            "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
            "Accept-Language": random.choice([
                "en-US,en;q=0.9",
                "en-GB,en-US;q=0.9,en;q=0.8",
                "en-US,en;q=0.5",
            ]),
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "image",
            "Sec-Fetch-Mode": "no-cors",
            "Sec-Fetch-Site": "cross-site",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        
        # Add random referer for better legitimacy
        if random.random() < 0.7:  # 70% chance to add referer
            referers = [
                f"https://www.google.com/search?q={domain}",
                f"https://{domain}/",
                "https://www.google.com/",
                "https://www.bing.com/",
                f"https://www.{domain}/",
            ]
            headers["Referer"] = random.choice(referers)
        
        # Randomly add some optional headers for realism
        if random.random() < 0.3:
            headers["X-Requested-With"] = "XMLHttpRequest"
        
        if random.random() < 0.4:
            headers["Priority"] = random.choice(["u=1", "u=2", "u=3"])
            
        return headers


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


@dataclass
class ImageMetadata:
    """Metadata for an image file."""
    file_path: str
    file_size: int
    width: int
    height: int
    format: str
    mode: Optional[str] = None
    file_hash: Optional[str] = None


@dataclass 
class ProcessingResult:
    """Result from image processing operation."""
    success: bool
    original_metadata: Optional[ImageMetadata]
    optimized_metadata: Optional[ImageMetadata] 
    thumbnail_metadata: Optional[ImageMetadata]
    error_message: Optional[str]
    temp_files: List[str]
    total_processing_time: float


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
        min_dimensions: Tuple[int, int] = (420, 420),
        max_dimensions: Tuple[int, int] = (10000, 10000),
        supported_formats: Optional[List[str]] = None,
        concurrent_downloads: int = 10,  # Reduced from 5 to respect DataImpulse limits
        use_proxy: bool = True,
        proxy_countries: Optional[List[str]] = None,
        use_sticky_sessions: bool = True  # Use sticky sessions by default
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
        self.use_sticky_sessions = use_sticky_sessions
        self.proxy_countries = proxy_countries or ['us', 'ca', None]  # Focus on working regions, None = random country
        
        # Session management for sticky proxies
        self.session_id = None
        if use_sticky_sessions:
            self.session_id = self.proxy_config.get_next_session_id()
        
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
        import ssl
        
        # Create SSL context that's more permissive for bot detection avoidance
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        connector = aiohttp.TCPConnector(
            limit=self.concurrent_downloads, 
            force_close=False,  # Don't force close to allow keepalive
            ssl=ssl_context,
            ttl_dns_cache=300,  # Cache DNS for 5 minutes
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )
        timeout = aiohttp.ClientTimeout(total=45, connect=15)
        
        # Don't set default headers - we'll use dynamic ones per request
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(),  # Accept cookies like a real browser
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
    
    def _get_proxy_url(self) -> str:
        """Get proxy URL using DataImpulse best practices."""
        country = random.choice(self.proxy_countries)
        
        if self.use_sticky_sessions and self.session_id:
            # Use sticky session for consistency (same IP for ~30min)
            return self.proxy_config.get_sticky_session_url(self.session_id, country)
        else:
            # Use rotating proxy (new IP each request)
            return self.proxy_config.get_rotating_http_url(country)
    
    async def _download_with_proxy(self, url: str, session_id: Optional[int] = None) -> ProxyDownloadResult:
        """
        Download image using proxy with retry logic and rotation.
        
        Args:
            url: Image URL to download
            session_id: Optional session ID for sticky proxy
            
        Returns:
            ProxyDownloadResult with download details
        """
        start_time = datetime.now()
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            proxy_url = None
            
            try:
                # Thread management - acquire slot before download
                if not self.proxy_config.acquire_thread():
                    raise Exception(f"Thread limit exceeded ({self.proxy_config.max_concurrent_threads})")
                
                try:
                    # Rate limiting and retry delays
                    if retry_count > 0:
                        logger.info(f"Retry {retry_count}/{max_retries} for {url} with new proxy")
                        await asyncio.sleep(1.5 * retry_count)  # Progressive backoff
                    
                    # Get proxy URL using DataImpulse best practices
                    proxy_url = self._get_proxy_url()
                    
                    # Generate realistic browser headers
                    headers = BrowserHeaders.get_random_headers(url)
                    
                    # Add random timing delay to appear more human-like
                    if retry_count == 0:  # Only delay on first attempt
                        delay = random.uniform(0.5, 2.0)
                        await asyncio.sleep(delay)
                    
                    # ALWAYS use proxy when enabled
                    kwargs = {
                        'timeout': aiohttp.ClientTimeout(total=45, connect=15),  # Increased timeouts
                        'headers': headers,
                        'allow_redirects': True,
                        'max_redirects': 3,
                    }
                    
                    if self.use_proxy and proxy_url:
                        kwargs['proxy'] = proxy_url
                        logger.info(f"Downloading via proxy with UA: {headers['User-Agent'][:60]}...")
                    else:
                        logger.warning(f"Proxy disabled or unavailable, direct download: {url}")
                    
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
                        proxy_used=proxy_url if self.use_proxy else "direct",
                        retry_count=retry_count
                    )
                    
                finally:
                    # Always release thread slot
                    self.proxy_config.release_thread()
                
            except Exception as e:
                last_error = str(e)
                retry_count += 1
                
                if retry_count < max_retries:
                    # Log retry attempt
                    if "403" in str(e) or "Forbidden" in str(e):
                        logger.warning(f"Got 403 Forbidden for {url}, rotating proxy...")
                    elif "timeout" in str(e).lower():
                        logger.warning(f"Timeout for {url}, trying new proxy...")
                    else:
                        logger.warning(f"Error downloading {url}: {e}, retrying...")
                    continue
                else:
                    # Final failure after all retries
                    self.download_stats['failed_downloads'] += 1
                    if proxy_url:
                        self.download_stats['proxy_failures'] += 1
                    
                    logger.error(f"Download failed for {url} after {max_retries} retries: {last_error}")
                    
                    return ProxyDownloadResult(
                        url=url,
                        success=False,
                        error=last_error,
                        proxy_used=proxy_url if self.use_proxy else "direct",
                        retry_count=retry_count
                    )
        
        # Should not reach here, but just in case
        self.download_stats['total_attempts'] += retry_count + 1
        return ProxyDownloadResult(
            url=url,
            success=False,
            error=last_error or "Unknown error",
            proxy_used="unknown",
            retry_count=retry_count
        )
    
    async def download_image(self, url: str, max_size_mb: Optional[int] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Download a single image (compatible with ImageProcessor interface).
        
        Args:
            url: Image URL to download
            max_size_mb: Maximum file size in MB (optional)
            
        Returns:
            Tuple of (success, file_path, error_message)
        """
        if not self.session:
            # Initialize session if not in async context
            await self.__aenter__()
        
        try:
            result = await self._download_with_proxy(url)
            
            if result.success and result.file_path:
                # Check file size if limit specified
                if max_size_mb:
                    file_size_mb = result.file_size / (1024 * 1024)
                    if file_size_mb > max_size_mb:
                        Path(result.file_path).unlink(missing_ok=True)
                        return False, None, f"File too large: {file_size_mb:.1f}MB > {max_size_mb}MB"
                
                return True, result.file_path, None
            else:
                return False, None, result.error or "Download failed"
                
        except Exception as e:
            logger.error(f"Error downloading {url}: {e}")
            return False, None, str(e)
    
    async def process_image(
        self,
        url: str,
        optimize: bool = True,
        generate_thumb: bool = True
    ) -> ProcessingResult:
        """
        Process a single image through proxy download and optimization.
        
        Args:
            url: Image URL to process
            optimize: Whether to optimize the image
            generate_thumb: Whether to generate thumbnail
            
        Returns:
            ProcessingResult with processing details
        """
        start_time = time.time()
        temp_files = []
        
        try:
            # Download image through proxy
            success, file_path, error = await self.download_image(url)
            
            if not success or not file_path:
                return ProcessingResult(
                    success=False,
                    original_metadata=None,
                    optimized_metadata=None,
                    thumbnail_metadata=None,
                    error_message=error or "Download failed",
                    temp_files=[],
                    total_processing_time=time.time() - start_time
                )
            
            temp_files.append(file_path)
            
            # Get image metadata
            try:
                with Image.open(file_path) as img:
                    original_metadata = ImageMetadata(
                        file_path=file_path,
                        file_size=Path(file_path).stat().st_size,
                        width=img.width,
                        height=img.height,
                        format=img.format or "UNKNOWN",
                        mode=img.mode
                    )
                    
                    # Calculate file hash
                    with open(file_path, 'rb') as f:
                        original_metadata.file_hash = hashlib.sha256(f.read()).hexdigest()
            except Exception as e:
                logger.error(f"Error reading image metadata: {e}")
                return ProcessingResult(
                    success=False,
                    original_metadata=None,
                    optimized_metadata=None,
                    thumbnail_metadata=None,
                    error_message=f"Failed to read image: {e}",
                    temp_files=temp_files,
                    total_processing_time=time.time() - start_time
                )
            
            # For now, skip optimization and thumbnail generation
            # These can be added later if needed
            optimized_metadata = None
            thumbnail_metadata = None
            
            return ProcessingResult(
                success=True,
                original_metadata=original_metadata,
                optimized_metadata=optimized_metadata,
                thumbnail_metadata=thumbnail_metadata,
                error_message=None,
                temp_files=temp_files,
                total_processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Error processing image {url}: {e}")
            return ProcessingResult(
                success=False,
                original_metadata=None,
                optimized_metadata=None,
                thumbnail_metadata=None,
                error_message=str(e),
                temp_files=temp_files,
                total_processing_time=time.time() - start_time
            )
    
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
                
                # At least one dimension should meet minimum requirement
                if width < min_w and height < min_h:
                    return False, f"Image too small: {width}x{height} (minimum: {min_w}x{min_h})"
                
                if width > max_w or height > max_h:
                    return False, f"Image too large: {width}x{height}"
                
                # Check aspect ratio (between 1:2 and 2:1)
                aspect_ratio = width / height
                if aspect_ratio < 0.5 or aspect_ratio > 2.0:
                    return False, f"Invalid aspect ratio: {width}x{height} (ratio: {aspect_ratio:.2f})"
                
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
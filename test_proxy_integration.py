#!/usr/bin/env python3
"""
Test script for proxy-enabled ImageFox downloads.
Verifies that DataImpulse proxies work with the ImageFox pipeline.
"""

import asyncio
import logging
from pathlib import Path

from proxy_image_processor import ProxyImageProcessor
from proxy_config import DataImpulseConfig

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_proxy_downloads():
    """Test downloading images through DataImpulse proxies."""
    
    # Test URLs from various sources
    test_urls = [
        "https://via.placeholder.com/800x600",
        "https://picsum.photos/1024/768",
        "https://images.unsplash.com/photo-1506905925346-21bda4d32df4",
        "https://cdn.pixabay.com/photo/2015/04/23/22/00/tree-736885_960_720.jpg"
    ]
    
    logger.info("=" * 60)
    logger.info("Testing ImageFox with DataImpulse Proxy Integration")
    logger.info("=" * 60)
    
    # Test proxy configuration
    config = DataImpulseConfig()
    logger.info(f"\nProxy Configuration:")
    logger.info(f"  Gateway: {config.gateway}")
    logger.info(f"  HTTP Port: {config.http_port}")
    logger.info(f"  Credentials Valid: {config.test_credentials()}")
    
    # Test with proxy enabled
    async with ProxyImageProcessor(
        proxy_config=config,
        use_proxy=True,
        concurrent_downloads=3
    ) as processor:
        
        logger.info("\n1. Testing proxy connectivity...")
        proxy_ok = await processor._test_proxy_connection()
        if proxy_ok:
            logger.info("✅ Proxy connection successful")
        else:
            logger.warning("⚠️ Proxy connection failed, will use direct connection")
        
        logger.info("\n2. Downloading test images through proxy...")
        results = await processor.process_and_download(
            test_urls[:2],  # Test with first 2 URLs
            validate=True
        )
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"\nDownload Results: {success_count}/{len(results)} successful")
        
        for i, result in enumerate(results, 1):
            if result.success:
                logger.info(f"  {i}. ✅ {result.url}")
                logger.info(f"     File: {result.file_path}")
                logger.info(f"     Size: {result.file_size:,} bytes")
                logger.info(f"     Time: {result.download_time:.2f}s")
                logger.info(f"     Proxy: {result.proxy_used}")
            else:
                logger.info(f"  {i}. ❌ {result.url}")
                logger.info(f"     Error: {result.error}")
        
        # Show statistics
        logger.info("\n3. Download Statistics:")
        stats = processor.get_stats()
        logger.info(f"  Total attempts: {stats.get('total_attempts', 0)}")
        logger.info(f"  Successful: {stats.get('successful_downloads', 0)}")
        logger.info(f"  Failed: {stats.get('failed_downloads', 0)}")
        logger.info(f"  Success rate: {stats.get('success_rate', 0):.1%}")
        
        if stats.get('avg_download_time'):
            logger.info(f"  Avg download time: {stats['avg_download_time']:.2f}s")
        if stats.get('avg_file_size'):
            logger.info(f"  Avg file size: {stats['avg_file_size']:,.0f} bytes")
        
        # Clean up temp files
        await processor.cleanup()
        logger.info("\n✅ Temporary files cleaned up")
    
    # Test without proxy for comparison
    logger.info("\n" + "=" * 60)
    logger.info("Testing without proxy for comparison...")
    logger.info("=" * 60)
    
    async with ProxyImageProcessor(use_proxy=False) as processor:
        results_direct = await processor.process_and_download(
            test_urls[:2],
            validate=True
        )
        
        success_direct = sum(1 for r in results_direct if r.success)
        logger.info(f"\nDirect Download Results: {success_direct}/{len(results_direct)} successful")
        
        await processor.cleanup()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    logger.info(f"Proxy downloads: {success_count}/{len(results)} successful")
    logger.info(f"Direct downloads: {success_direct}/{len(results_direct)} successful")
    
    if success_count > 0:
        logger.info("\n✅ Proxy integration is working correctly!")
    else:
        logger.warning("\n⚠️ Proxy downloads failed, check configuration")


if __name__ == "__main__":
    asyncio.run(test_proxy_downloads())
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Example usage of the Firecrawl tool with MetaGPT."""

import asyncio
import os
import sys
from pathlib import Path
import time

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from metagpt.tools.libs.firecrawl import Firecrawl

async def main():
    """Run example usage of Firecrawl tool."""
    # Set up environment variables if not already set
    if "FIRECRAWL_API_KEY" not in os.environ:
        os.environ["FIRECRAWL_API_KEY"] = "YOUR-FIRECRAWL-API-KEY"

    # Create Firecrawl instance
    firecrawl = Firecrawl()

    # Example 1: Search for information
    print("\nExample 1: Search for Therapist in Portugal by name")
    search_results = await firecrawl.search("Psicologa Clínica Mairí Stumpf")
    print("Search Results:", search_results)

    # Example 2: Map and crawl a website
    print("\nExample 2: Map and crawl a website")
    map_results = await firecrawl.map_url("https://docs.firecrawl.dev")
    print("Map Results:", map_results)
    
    if map_results.get("links"):
        crawl_job = await firecrawl.crawl_url(map_results["links"][0])
        print("Crawl Job:", crawl_job)
        
        if crawl_job.get("id"):
            status = await firecrawl.get_crawl_status(crawl_job["id"])
            print("Crawl Status:", status)
            # While the status is not "completed" we can loop and print the status
            while status.get("status") != "completed":
                status = await firecrawl.get_crawl_status(crawl_job["id"])
                print("Crawl Status:", status)
                await asyncio.sleep(5)

    # Example 3: Scrape a specific URL
    print("\nExample 3: Scrape a URL")
    scrape_results = await firecrawl.scrape_url("https://example.com")
    print("Scrape Results:", scrape_results)
    
    # Example 4: Extract information from URLs
    print("\nExample 4: Extract information")
    extract_job = await firecrawl.extract(
        ["https://www.imdb.com/chart/starmeter/"], 
        params={"prompt": "Extract the top five most popular celebs names and their popularity score if available"}
    )
    print("Extract Job:", extract_job)
    
    if extract_job.get("id"):
        extract_status = await firecrawl.get_extract_status(extract_job["id"])
        print("\nExtract Status:", extract_status)

        # While the status is not "completed" we can loop and print the status
        while extract_status.get("status") != "completed":
            extract_status = await firecrawl.get_extract_status(extract_job["id"])
            print("\nUpdated Status:", extract_status)
            await asyncio.sleep(10)

if __name__ == "__main__":
    asyncio.run(main()) 
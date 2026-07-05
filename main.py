from scraper import run_scraper
from ai_sync import AISyncManager

def main():
    print("Starting OptiBot Mini-Clone Sync Job...")
    
    print("Phase 1: Scraping articles with priority keywords...")
    scraped_count = run_scraper(priority_keyword="youtube")
    print(f"Scraped {scraped_count} articles in total.")
    
    print("Phase 2: Synchronizing with AI Vector Store...")
    sync_manager = AISyncManager()
    added, updated, skipped = sync_manager.sync_directory()
    
    print("Job completed successfully.")
    print(f"Summary -> Added: {added}, Updated: {updated}, Skipped: {skipped}")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
# app/scripts/seed.py

"""
Database Seeder CLI

Usage:
    python app/scripts/seed.py                      # Run all seeders
    python app/scripts/seed.py --reset              # Reset database and reseed
    python app/scripts/seed.py --restore            # Restore from latest backup
    python app/scripts/seed.py --restore --key KEY  # Restore from specific backup
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse

from app.database import AsyncSessionLocal
from app.modules.seeder.services import SeederService
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


async def run_seeders():
    """Run all seeders."""
    async with AsyncSessionLocal() as db:
        service = SeederService(db)
        
        logger.info("Starting database seeding...")
        print("🌱 Starting database seeding...")
        
        try:
            result = await service.execute_seeder(
                create_backup=True,
                user_id=None
            )
            
            print("\n✅ Seeding completed successfully!")
            print(f"📦 Backup created: {result['backup_s3_key']}")
            print(f"\n📊 Results:")
            
            for seeder_name, stats in result['results']['seeders'].items():
                print(f"  • {seeder_name}:")
                print(f"    - Created: {stats['created']}")
                print(f"    - Updated: {stats['updated']}")
                print(f"    - Status: {stats['status']}")
            
            total = result['results']['total']
            print(f"\n🎯 Total:")
            print(f"  - Created: {total['created']}")
            print(f"  - Updated: {total['updated']}")
            
        except Exception as e:
            print(f"\n❌ Seeding failed: {str(e)}")
            logger.error("seeding_failed", error=str(e))
            sys.exit(1)


async def reset_database():
    """Reset database and reseed."""
    async with AsyncSessionLocal() as db:
        service = SeederService(db)
        
        print("⚠️  WARNING: This will delete ALL data and reseed the database!")
        confirm = input("Type 'RESET' to confirm: ")
        
        if confirm != "RESET":
            print("❌ Reset cancelled.")
            return
        
        logger.info("Starting database reset...")
        print("\n🔄 Starting database reset...")
        
        try:
            result = await service.reset_database(user_id=None)
            
            print("\n✅ Reset completed successfully!")
            print(f"📦 Backup created: {result['backup_s3_key']}")
            print(f"\n📊 Results:")
            
            for seeder_name, stats in result['results']['seeders'].items():
                print(f"  • {seeder_name}:")
                print(f"    - Created: {stats['created']}")
                print(f"    - Status: {stats['status']}")
            
        except Exception as e:
            print(f"\n❌ Reset failed: {str(e)}")
            logger.error("reset_failed", error=str(e))
            sys.exit(1)


async def restore_database(s3_key: str = None):
    """Restore database from backup."""
    async with AsyncSessionLocal() as db:
        service = SeederService(db)
        
        if s3_key:
            print(f"📦 Restoring from backup: {s3_key}")
        else:
            print("📦 Restoring from latest backup...")
        
        print("\n⚠️  WARNING: This will replace current data with backup!")
        confirm = input("Type 'RESTORE' to confirm: ")
        
        if confirm != "RESTORE":
            print("❌ Restore cancelled.")
            return
        
        logger.info("Starting database restore...")
        print("\n🔄 Starting database restore...")
        
        try:
            result = await service.restore_from_backup(
                s3_key=s3_key,
                user_id=None
            )
            
            print("\n✅ Restore completed successfully!")
            print(f"📦 Restored from: {result['s3_key']}")
            print(f"📊 Statistics:")
            print(f"  - Tables restored: {result['tables_restored']}")
            print(f"  - Records restored: {result['records_restored']}")
            
        except Exception as e:
            print(f"\n❌ Restore failed: {str(e)}")
            logger.error("restore_failed", error=str(e))
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Database Seeder CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database and reseed (WARNING: deletes all data)'
    )
    
    parser.add_argument(
        '--restore',
        action='store_true',
        help='Restore database from backup'
    )
    
    parser.add_argument(
        '--key',
        type=str,
        help='S3 key of backup to restore (use with --restore)'
    )
    
    args = parser.parse_args()
    
    if args.reset:
        asyncio.run(reset_database())
    elif args.restore:
        asyncio.run(restore_database(s3_key=args.key))
    else:
        asyncio.run(run_seeders())


if __name__ == "__main__":
    main()
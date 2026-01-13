#!/usr/bin/env python3
"""
Ivoris Daily Extraction Pipeline

Extracts chart entries (Karteikarteneintrag) with patient, insurance,
and service information for daily data transfer.

Usage:
    python src/main.py --daily-extract
    python src/main.py --daily-extract --date 2026-01-12
    python src/main.py --daily-extract --format csv
"""

import argparse
import logging
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
from src.adapters.database import DatabaseAdapter
from src.services.daily_extract import DailyExtractService

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Ivoris Daily Extraction Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --daily-extract
    %(prog)s --daily-extract --date 2026-01-12
    %(prog)s --daily-extract --format csv
    %(prog)s --test-connection
        """
    )

    parser.add_argument(
        '--daily-extract',
        action='store_true',
        help='Run daily chart entry extraction'
    )

    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Target date (YYYY-MM-DD, default: yesterday)'
    )

    parser.add_argument(
        '-f', '--format',
        choices=['csv', 'json', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    parser.add_argument(
        '--test-connection',
        action='store_true',
        help='Test database connection'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    return parser.parse_args()


def test_connection() -> bool:
    """Test database connection."""
    logger.info("Testing database connection...")
    db = DatabaseAdapter(
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
        user=settings.DB_USER,
        password=settings.DB_PASSWORD
    )
    try:
        if db.test_connection():
            logger.info("Connection successful!")
            db.disconnect()
            return True
        else:
            logger.error("Connection failed")
            return False
    except Exception as e:
        logger.error(f"Connection error: {e}")
        return False


def main() -> int:
    """Main entry point."""
    args = parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info(f"Starting {settings.PROJECT_NAME}")

    # Test connection
    if args.test_connection:
        return 0 if test_connection() else 1

    # Daily extraction
    if args.daily_extract:
        # Validate settings
        errors = settings.validate()
        if errors:
            for error in errors:
                logger.error(f"Config error: {error}")
            return 1

        # Parse target date
        target_date = None
        if args.date:
            try:
                target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            except ValueError:
                logger.error(f"Invalid date: {args.date}. Use YYYY-MM-DD")
                return 1
        else:
            target_date = date.today() - timedelta(days=1)

        # Connect to database
        db = DatabaseAdapter(
            host=settings.DB_HOST,
            port=settings.DB_PORT,
            database=settings.DB_NAME,
            user=settings.DB_USER,
            password=settings.DB_PASSWORD
        )

        if not db.test_connection():
            logger.error("Could not connect to database")
            return 1

        # Run extraction
        service = DailyExtractService(db, settings.OUTPUT_DIR)
        result = service.run(target_date=target_date, output_format=args.format)

        # Report results
        logger.info(f"Target date: {result['target_date']}")
        logger.info(f"Records: {result['record_count']}")
        for fmt, path in result['output_files'].items():
            logger.info(f"Output: {path}")

        db.disconnect()
        return 0

    # No action specified
    logger.info("No action specified. Use --help for options.")
    return 0


if __name__ == '__main__':
    sys.exit(main())

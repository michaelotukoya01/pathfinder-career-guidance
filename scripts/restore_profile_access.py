"""Issue a replacement device token for a profile you administer locally.

Usage: python scripts/restore_profile_access.py PROFILE_UUID
The output is a credential. Keep it private and paste it into Dashboard > Restore access.
"""
import argparse
import hashlib
import json
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')
from profile_store import profile_store


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile_id')
    args = parser.parse_args()
    if not profile_store.get_profile(args.profile_id):
        parser.error('Profile not found')
    token = secrets.token_urlsafe(32)
    profile_store.update_profile(args.profile_id, {'_access_token_hash': hashlib.sha256(token.encode()).hexdigest()})
    print(json.dumps({'profile_id': args.profile_id, 'access_token': token}, indent=2))


if __name__ == '__main__':
    main()

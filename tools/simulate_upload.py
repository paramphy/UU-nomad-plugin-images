#!/usr/bin/env python3
"""Simulate uploading a sample archive to a NOMAD server.

This script performs a multipart POST with a file field (default name: `file`) to
the given upload endpoint. It's intentionally flexible: configure the endpoint URL,
the multipart field name, and an authorization token if your NOMAD instance requires it.

Example (PowerShell):
  python .\tools\simulate_upload.py --url http://localhost:8080/api/uploads C:\path\to\sample.zip

Include an auth token:
  python .\tools\simulate_upload.py --url http://localhost:8080/api/uploads --token "sometoken" --token-type Token sample.zip

If you need to send extra metadata (JSON), pass a JSON string or a path to a JSON file with --extra
  python .\tools\simulate_upload.py --extra '{"uploader":"me"}' sample.zip

Notes:
- The exact upload endpoint and field name may vary depending on your NOMAD deployment. Provide the
  full URL via `--url` and change `--field` if necessary.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Optional

import requests


def load_json_or_string(value: str) -> str:
    # If value is a path to a file, load it; otherwise treat as a JSON string
    if os.path.exists(value):
        with open(value, 'r', encoding='utf-8') as f:
            return json.dumps(json.load(f))
    # Validate it's JSON
    try:
        json.loads(value)
        return value
    except Exception:
        raise ValueError('Provided --extra value is neither a path to a JSON file nor valid JSON string')


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description='Simulate upload of an archive to a NOMAD server')
    parser.add_argument('file', help='Path to the archive file to upload (e.g. sample.zip)')
    parser.add_argument('--url', default='http://localhost:8080/api/uploads',
                        help='Full upload endpoint URL (default: http://localhost:8080/api/uploads)')
    parser.add_argument('--field', default='file', help='Multipart field name for the file (default: file)')
    parser.add_argument('--token', help='Authentication token to set in the Authorization header')
    parser.add_argument('--token-type', choices=['Bearer', 'Token', 'Basic'], default='Bearer',
                        help='Authorization scheme to use with --token (default: Bearer)')
    parser.add_argument('--extra', help='Extra metadata: JSON string or path to JSON file (sent as form field "metadata")')
    parser.add_argument('--timeout', type=int, default=60, help='Request timeout in seconds')

    args = parser.parse_args(argv)

    if not os.path.exists(args.file):
        print(f'ERROR: file not found: {args.file}', file=sys.stderr)
        return 2

    headers = {}
    if args.token:
        headers['Authorization'] = f"{args.token_type} {args.token}"

    # Prepare files and data
    file_tuple = (os.path.basename(args.file), open(args.file, 'rb'), 'application/zip')
    files = {args.field: file_tuple}
    data = {}
    if args.extra:
        try:
            data['metadata'] = load_json_or_string(args.extra)
        except ValueError as e:
            print(f'ERROR: {e}', file=sys.stderr)
            return 3

    print(f'Uploading {args.file} -> {args.url} as field "{args.field}"')
    try:
        resp = requests.post(args.url, files=files, data=data, headers=headers, timeout=args.timeout)
    except requests.RequestException as e:
        print('Request failed:', e, file=sys.stderr)
        return 4
    finally:
        try:
            files[args.field][1].close()
        except Exception:
            pass

    print('HTTP', resp.status_code)
    # Print a truncated response for readability
    text = resp.text
    if len(text) > 4000:
        print(text[:4000] + '\n...[truncated]')
    else:
        print(text)

    # return non-zero for HTTP errors
    return 0 if resp.ok else 5


if __name__ == '__main__':
    raise SystemExit(main())

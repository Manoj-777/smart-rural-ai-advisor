#!/usr/bin/env python3
import argparse
import os
import re
from collections import defaultdict
from datetime import datetime

import boto3


CANONICAL_FARMER_ID_PATTERN = re.compile(r'^ph_[6-9]\d{9}$')


def parse_timestamp(value):
    if not value:
        return datetime.min
    text = str(value).strip().replace('Z', '+00:00')
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return datetime.min


def normalize_phone_from_item(item):
    for field in ('phone_normalized', 'phone', 'phone_number', 'mobile'):
        raw = item.get(field)
        if raw is None:
            continue
        digits = re.sub(r'\D', '', str(raw))
        if len(digits) >= 10:
            candidate = digits[-10:]
            if re.match(r'^[6-9]\d{9}$', candidate):
                return candidate

    farmer_id = str(item.get('farmer_id', '')).strip()
    if CANONICAL_FARMER_ID_PATTERN.match(farmer_id):
        return farmer_id[3:]

    return None


def keeper_sort_key(item, phone):
    farmer_id = str(item.get('farmer_id', '')).strip()
    is_canonical = 1 if farmer_id == f'ph_{phone}' else 0
    updated = parse_timestamp(item.get('updated_at'))
    created = parse_timestamp(item.get('created_at'))
    return (is_canonical, updated, created, farmer_id)


def scan_all(table):
    items = []
    scan_kwargs = {}
    while True:
        response = table.scan(**scan_kwargs)
        items.extend(response.get('Items', []))
        if 'LastEvaluatedKey' not in response:
            break
        scan_kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    return items


def main():
    parser = argparse.ArgumentParser(description='Detect and optionally dedupe farmer profiles by phone number.')
    parser.add_argument('--table', default=os.environ.get('DYNAMODB_PROFILES_TABLE', 'farmer_profiles'))
    parser.add_argument('--region', default=os.environ.get('AWS_REGION', 'ap-south-1'))
    parser.add_argument('--apply', action='store_true', help='Delete duplicate profiles (dry-run if omitted).')
    args = parser.parse_args()

    dynamodb = boto3.resource('dynamodb', region_name=args.region)
    table = dynamodb.Table(args.table)

    items = scan_all(table)
    grouped = defaultdict(list)

    for item in items:
        phone = normalize_phone_from_item(item)
        if not phone:
            continue
        grouped[phone].append(item)

    duplicate_groups = {phone: rows for phone, rows in grouped.items() if len(rows) > 1}

    if not duplicate_groups:
        print('No duplicate phone groups found.')
        return

    print(f'Found {len(duplicate_groups)} phone numbers with duplicate profiles.')

    total_to_delete = 0
    for phone, rows in sorted(duplicate_groups.items()):
        ordered = sorted(rows, key=lambda row: keeper_sort_key(row, phone), reverse=True)
        keep = ordered[0]
        drop = ordered[1:]
        keep_id = str(keep.get('farmer_id', ''))

        print(f'\nPhone {phone}: keep {keep_id}')
        for row in drop:
            drop_id = str(row.get('farmer_id', ''))
            updated = row.get('updated_at', '-')
            created = row.get('created_at', '-')
            print(f'  drop {drop_id} (updated_at={updated}, created_at={created})')

        total_to_delete += len(drop)

        if args.apply:
            for row in drop:
                drop_id = str(row.get('farmer_id', '')).strip()
                if not drop_id:
                    continue
                table.delete_item(Key={'farmer_id': drop_id})

    action = 'Deleted' if args.apply else 'Would delete'
    print(f'\n{action} {total_to_delete} duplicate profile item(s).')


if __name__ == '__main__':
    main()

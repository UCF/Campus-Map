# -*- coding: utf-8 -*-
"""
Management command to bulk import/update map locations from an xlsx file.

Usage:
    python manage.py import_xlsx <path/to/file.xlsx> [options]

Options:
    --sheet     Sheet name to read (default: New)
    --model     Model type: building, location, parkinglot, regionalcampus,
                bikerack, emergencyphone, emergencyaed, electricchargingstation
                (default: building)
    --dry-run   Preview changes without writing to the database

Column mapping (xlsx → model field):
    Title       → name
    Description → profile  (HTML field; also sets description if <= 255 chars)
    Reference   → abbreviation; used as the primary upsert key
    Location    → googlemap_point  (converts "lat,lon" → "[lat, lon]")

Upsert strategy (in order):
    1. Match existing record by abbreviation == Reference
    2. Match existing record by id == Reference.lower()
    3. Match existing record by name == Title  (when Reference is blank)
    4. Create new record (id = Reference.lower() or slugify(Title))
"""
from __future__ import unicode_literals

import os

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

try:
    import xlrd
except ImportError:
    raise ImportError(
        'xlrd is required. Install it with: pip install "xlrd==1.2.0"'
    )

from campus.models import (
    BikeRack,
    Building,
    ElectricChargingStation,
    EmergencyAED,
    EmergencyPhone,
    Location,
    ParkingLot,
    RegionalCampus,
)

MODEL_MAP = {
    'building': Building,
    'location': Location,
    'parkinglot': ParkingLot,
    'regionalcampus': RegionalCampus,
    'bikerack': BikeRack,
    'emergencyphone': EmergencyPhone,
    'emergencyaed': EmergencyAED,
    'electricchargingstation': ElectricChargingStation,
}


def _cell_str(row, idx):
    """Return a stripped unicode string from a cell, or '' if missing/blank."""
    if idx is None or idx >= len(row):
        return ''
    val = row[idx]
    if val is None:
        return ''
    return unicode(val).strip()


def _parse_coordinates(location_str):
    """
    Convert 'lat,lon' string to '[lat, lon]' format expected by googlemap_point.
    Returns None if the string cannot be parsed.
    """
    if not location_str:
        return None
    try:
        parts = location_str.split(',')
        lat = float(parts[0].strip())
        lon = float(parts[1].strip())
        return '[%s, %s]' % (lat, lon)
    except (ValueError, IndexError):
        return None


class Command(BaseCommand):
    help = 'Import or update map locations from an xlsx bulk-upload file'

    def add_arguments(self, parser):
        parser.add_argument(
            'xlsx_file',
            help='Path to the .xlsx file',
        )
        parser.add_argument(
            '--sheet',
            default='New',
            dest='sheet',
            help='Sheet name to read (default: New)',
        )
        parser.add_argument(
            '--model',
            default='building',
            dest='model',
            choices=list(MODEL_MAP.keys()),
            help='Model type to create/update (default: building)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            dest='dry_run',
            help='Preview changes without writing to the database',
        )

    def handle(self, *args, **options):
        path = options['xlsx_file']
        sheet_name = options['sheet']
        model_key = options['model']
        dry_run = options['dry_run']

        Model = MODEL_MAP[model_key]

        # --- Open workbook ---------------------------------------------------
        if not os.path.isfile(path):
            raise CommandError('File not found: %s' % path)

        try:
            wb = xlrd.open_workbook(path)
        except Exception as e:
            raise CommandError('Could not open workbook: %s' % str(e))

        try:
            ws = wb.sheet_by_name(sheet_name)
        except xlrd.biffh.XLRDError:
            available = ', '.join(wb.sheet_names())
            raise CommandError(
                'Sheet "%s" not found. Available sheets: %s' % (sheet_name, available)
            )

        if ws.nrows < 2:
            self.stdout.write('Sheet "%s" has no data rows.' % sheet_name)
            return

        # --- Build column index map -----------------------------------------
        headers = [h.strip() for h in ws.row_values(0)]
        col = {h: i for i, h in enumerate(headers) if h}

        for required_col in ('Title', 'Location'):
            if required_col not in col:
                raise CommandError(
                    'Required column "%s" not found in sheet "%s". '
                    'Found columns: %s' % (required_col, sheet_name, ', '.join(col.keys()))
                )

        if dry_run:
            self.stdout.write('*** DRY RUN — no changes will be saved ***\n')

        created = 0
        updated = 0
        skipped = 0

        # --- Process rows ---------------------------------------------------
        for row_num in range(1, ws.nrows):
            row = ws.row_values(row_num)

            title = _cell_str(row, col.get('Title'))
            description = _cell_str(row, col.get('Description'))
            reference = _cell_str(row, col.get('Reference'))
            location_str = _cell_str(row, col.get('Location'))

            if not title:
                self.stdout.write('  Row %d: skipping — no title' % (row_num + 1))
                skipped += 1
                continue

            # Parse coordinates
            googlemap_point = _parse_coordinates(location_str)
            if location_str and googlemap_point is None:
                self.stdout.write(
                    '  Row %d: unrecognised location format "%s" — coordinates skipped'
                    % (row_num + 1, location_str)
                )

            # --- Upsert lookup ----------------------------------------------
            obj = None
            is_new = False

            if reference:
                # 1. Match by abbreviation
                matches = Model.objects.filter(abbreviation=reference)
                if matches.count() == 1:
                    obj = matches[0]
                elif matches.count() > 1:
                    self.stdout.write(
                        '  Row %d: WARNING — multiple %s records share '
                        'abbreviation "%s"; skipping row'
                        % (row_num + 1, model_key, reference)
                    )
                    skipped += 1
                    continue

                # 2. Match by id == reference.lower()
                if obj is None:
                    try:
                        obj = Model.objects.get(id=reference.lower())
                    except Model.DoesNotExist:
                        pass

                # 3. Create new with reference as id
                if obj is None:
                    obj = Model(id=reference.lower())
                    is_new = True

            else:
                # No reference — match by name
                matches = Model.objects.filter(name=title)
                if matches.count() == 1:
                    obj = matches[0]
                elif matches.count() > 1:
                    self.stdout.write(
                        '  Row %d: WARNING — multiple %s records share '
                        'name "%s"; skipping row'
                        % (row_num + 1, model_key, title)
                    )
                    skipped += 1
                    continue

                if obj is None:
                    generated_id = slugify(title)[:80]
                    obj = Model(id=generated_id)
                    is_new = True

            # --- Apply field values -----------------------------------------
            obj.name = title

            if description:
                obj.profile = description
                if len(description) <= 255:
                    obj.description = description

            if reference:
                obj.abbreviation = reference

            if googlemap_point:
                obj.googlemap_point = googlemap_point

            # --- Save -------------------------------------------------------
            action = 'CREATE' if is_new else 'UPDATE'
            self.stdout.write('%s [%-8s] %s' % (action, getattr(obj, 'id', '?'), title))

            if not dry_run:
                try:
                    obj.save()
                    if is_new:
                        created += 1
                    else:
                        updated += 1
                except Exception as e:
                    self.stdout.write(
                        '  ERROR on row %d (%s): %s' % (row_num + 1, title, str(e))
                    )
                    skipped += 1
            else:
                if is_new:
                    created += 1
                else:
                    updated += 1

        # --- Summary --------------------------------------------------------
        suffix = ' (dry run — nothing saved)' if dry_run else ''
        self.stdout.write(
            '\nFinished%s: %d created, %d updated, %d skipped.'
            % (suffix, created, updated, skipped)
        )
